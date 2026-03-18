from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QTextEdit,
)

from app_state.projections import find_page
from app_state.ui_state import UiState
from core.enums import RowType
from core.page_lock import BlockLockedError, PageLockedError
from services.controller import BancaController
from services.mobile_backend_manager import MobileBackendManager
from services.mobile_share import (
    DEFAULT_MOBILE_PORT,
    build_mobile_share_url,
    detect_local_network_ip,
    is_mobile_backend_reachable,
)
from services.whatsapp_service import WhatsAppService
from ui.delegates.bet_delegate import BetDelegate
from ui.delegates.contact_delegate import ContactDelegate
from ui.delegates.value_delegate import ValueDelegate
from ui.dialogs.block_dialog import BlockDialog
from ui.dialogs.confirm_dialog import ask_confirmation
from ui.dialogs.result_dialog import ResultDialog
from ui.dialogs.session_name_dialog import SessionNameDialog
from ui.dialogs.value_dialog import ValueDialog
from ui.dialogs.whatsapp_dialog import WhatsAppDialog
from ui.models.bets_table_model import BetsTableModel
from ui.models.finance_table_model import FinanceTableModel
from ui.views.bets_table_view import BetsTableView
from ui.views.finance_table_view import FinanceTableView
from ui.widgets.bottom_bar import BottomBar
from ui.widgets.finance_totals_panel import FinanceTotalsPanel
from ui.widgets.pendency_panel import PendencyPanel
from ui.widgets.result_panel import ResultPanel
from ui.widgets.session_overview_panel import SessionOverviewPanel

APP_NAME = "Conferix"


class MainWindow(QMainWindow):
    def __init__(
        self,
        controller: BancaController,
        root: Path,
        parent=None,
        mobile_backend_manager: MobileBackendManager | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.root = root
        self.mobile_backend_manager = mobile_backend_manager
        self.whatsapp_service = WhatsAppService()
        self._contact_menu: QMenu | None = None
        self._startup_focus_pending = True
        self._syncing_block_search = False
        self.setWindowTitle(APP_NAME)
        self.resize(1500, 920)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        QApplication.instance().installEventFilter(self)

        self.bets_model = BetsTableModel(self.controller)
        self.finance_model = FinanceTableModel(self.controller)

        self.bets_view = BetsTableView(self.controller, self)
        self.bets_view.setObjectName("betsTable")
        self.bets_view.setModel(self.bets_model)
        self.bets_view.setItemDelegateForColumn(0, BetDelegate(self.bets_view))
        self.bets_view.setItemDelegateForColumn(1, ValueDelegate(self.bets_view))
        self.bets_view.horizontalHeader().setStretchLastSection(False)
        self.bets_view.horizontalHeader().setMinimumSectionSize(84)
        self.bets_view.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.bets_view.setColumnWidth(1, 118)
        self.bets_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bets_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.bets_view.horizontalHeader().hide()
        self.bets_view.createBlockRequested.connect(self.handle_create_block)
        self.bets_view.createPageRequested.connect(self.handle_create_page)
        self.bets_view.lockConflict.connect(self.handle_locked_action)
        self.bets_view.deletePageRequested.connect(self.handle_delete_page)
        self.bets_view.deleteBlockRequested.connect(self.handle_delete_block)

        self.finance_view = FinanceTableView(self)
        self.finance_view.setObjectName("financeTable")
        self.finance_view.setModel(self.finance_model)
        self.finance_view.setItemDelegateForColumn(
            FinanceTableModel.COL_CONTACT, ContactDelegate(self.finance_view)
        )
        self.finance_view.setItemDelegateForColumn(
            FinanceTableModel.COL_RECEIVED, ValueDelegate(self.finance_view, finance=True)
        )
        for column in range(self.finance_model.columnCount()):
            self.finance_view.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        self.finance_view.contactMenuRequested.connect(self.handle_contact_menu)
        self.finance_view.blockNavigationRequested.connect(self.handle_focus_block)
        self.finance_view.lockConflict.connect(self.handle_locked_action)

        self.result_panel = ResultPanel(self)
        self.overview_panel = SessionOverviewPanel(self)
        self.overview_panel.blockNavigationRequested.connect(self.handle_focus_block)
        self.pending_panel = PendencyPanel(self)
        self.finance_totals_panel = FinanceTotalsPanel(self)
        self.finance_totals_panel.totalPaidPrizesChanged.connect(self.handle_total_paid_prizes_change)
        self.finance_totals_panel.sessionNotesChanged.connect(self.handle_session_notes_change)

        self.bottom_bar = BottomBar(self)
        self.bottom_bar.blockSelected.connect(self.handle_bottom_block_selected)
        status_bar = QStatusBar(self)
        status_bar.setSizeGripEnabled(False)
        status_bar.setFixedHeight(46)
        status_bar.addPermanentWidget(self.bottom_bar, 1)
        self.setStatusBar(status_bar)

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(60_000)
        self.clock_timer.timeout.connect(self.update_window_clock)
        self.external_sync_timer = QTimer(self)
        self.external_sync_timer.setInterval(1_500)
        self.external_sync_timer.timeout.connect(self.sync_external_mobile_values)
        self._pending_finance_refresh_block_ids: set[str] = set()

        self._build_toolbar()
        self._build_layout()
        self.result_shortcut = QShortcut("F9", self)
        self.result_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.result_shortcut.activated.connect(self.handle_result_dialog)
        self.fullscreen_shortcut = QShortcut("F11", self)
        self.fullscreen_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        self.controller.subscribe(self.refresh_panels)
        self._startup_mobile_backend_result = self._ensure_mobile_backend_running()
        self.controller.ensure_bootstrap()
        self.refresh_panels()
        self.update_window_clock()
        self.clock_timer.start()
        self.external_sync_timer.start()
        self._restore_initial_focus()
        if self._startup_mobile_backend_result is not None:
            QTimer.singleShot(0, self._show_mobile_backend_startup_feedback)
        QTimer.singleShot(0, self._maybe_offer_runtime_resume)

    def eventFilter(self, watched, event):  # noqa: N802
        focus_widget = QApplication.focusWidget()
        block_search_line_edit = self.block_search_input.lineEdit() if hasattr(self, "block_search_input") else None
        if (
            watched is block_search_line_edit
            and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        ):
            self.handle_block_search()
            event.accept()
            return True
        if (
            event.type() == QEvent.Type.KeyPress
            and self.isVisible()
            and self.isActiveWindow()
            and event.key() == Qt.Key.Key_B
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and not isinstance(focus_widget, (QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox))
        ):
            self.handle_create_block()
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._startup_focus_pending:
            return
        self._startup_focus_pending = False
        QTimer.singleShot(0, self._prime_keyboard_focus)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._capture_ui_state()
        self.external_sync_timer.stop()
        self.clock_timer.stop()
        if self.mobile_backend_manager is not None:
            self.mobile_backend_manager.stop()
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def _prime_keyboard_focus(self) -> None:
        self.raise_()
        self.activateWindow()
        if self.bets_model.rowCount() > 0:
            self.bets_view.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            return
        if self.centralWidget() is not None:
            self.centralWidget().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.centralWidget().setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal", self)
        toolbar.setMovable(False)
        toolbar.setObjectName("mainToolbar")
        toolbar.setFixedHeight(64)
        self.addToolBar(toolbar)

        open_old_action = QAction("Abrir sessão salva...", self)
        open_old_action.triggered.connect(self.handle_open)
        open_old_action.setToolTip("Abrir uma sessão salva e substituir a atual.")
        open_old_action.setStatusTip(open_old_action.toolTip())
        save_action = QAction("Salvar", self)
        save_action.triggered.connect(self.handle_save)
        save_action.setToolTip("Salvar a sessão atual sem fechar a tela.")
        save_action.setStatusTip(save_action.toolTip())
        end_action = QAction("Encerrar sessão", self)
        end_action.triggered.connect(self.handle_end_session)
        end_action.setToolTip("Salvar e encerrar a sessão atual.")
        end_action.setStatusTip(end_action.toolTip())
        new_action = QAction("Nova sessão...", self)
        new_action.triggered.connect(self.handle_new_session)
        new_action.setToolTip("Abrir uma sessão nova e pedir o nome logo em seguida.")
        new_action.setStatusTip(new_action.toolTip())
        session_name_action = QAction("Renomear sessão...", self)
        session_name_action.triggered.connect(self.handle_session_name)
        session_name_action.setToolTip("Alterar o nome da sessão atual.")
        session_name_action.setStatusTip(session_name_action.toolTip())
        share_session_action = QAction("Compartilhar", self)
        share_session_action.triggered.connect(self.handle_share_session)
        share_session_action.setToolTip("Copiar o link da sessão para abrir no celular.")
        share_session_action.setStatusTip(share_session_action.toolTip())
        fill_page_action = QAction("Preencher", self)
        fill_page_action.triggered.connect(self.handle_apply_page_value)
        fill_page_action.setToolTip("Aplicar o mesmo valor a toda a página selecionada.")
        fill_page_action.setStatusTip(fill_page_action.toolTip())
        result_action = QAction("Resultado", self)
        result_action.triggered.connect(self.handle_result_dialog)
        result_action.setToolTip("Informar o resultado do sorteio (F9).")
        result_action.setStatusTip(result_action.toolTip())

        session_menu = QMenu(self)
        session_menu.setObjectName("sessionMenu")
        session_menu.addAction(open_old_action)
        session_menu.addAction(new_action)
        session_menu.addAction(save_action)
        session_menu.addAction(session_name_action)
        session_menu.addSeparator()
        session_menu.addAction(end_action)

        session_button = QToolButton(self)
        session_button.setObjectName("sessionMenuButton")
        session_button.setText("Sessão")
        session_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        session_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        session_button.setMenu(session_menu)
        session_button.setToolTip("Abrir, salvar, renomear ou encerrar a sessão atual.")
        toolbar.addWidget(session_button)

        toolbar.addAction(save_action)
        toolbar.addSeparator()
        toolbar.addAction(share_session_action)
        toolbar.addAction(fill_page_action)

        left_spacer = QWidget(self)
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(left_spacer)

        title_widget = QWidget(self)
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)
        self.title_label = QLabel(APP_NAME, title_widget)
        self.title_label.setProperty("topTitle", True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label)
        self.title_meta_label = QLabel("", title_widget)
        self.title_meta_label.setProperty("toolbarMeta", True)
        self.title_meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_meta_label)
        toolbar.addWidget(title_widget)

        right_spacer = QWidget(self)
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(right_spacer)

        search_widget = QWidget(self)
        search_widget.setObjectName("toolbarSearchWidget")
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(6)
        search_label = QLabel("Buscar bloco", search_widget)
        search_label.setProperty("toolbarLabel", True)
        self.block_search_input = QComboBox(search_widget)
        self.block_search_input.setObjectName("toolbarBlockSearch")
        self.block_search_input.setEditable(True)
        self.block_search_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.block_search_input.setMaxVisibleItems(16)
        self.block_search_input.setFixedWidth(196)
        self.block_search_input.lineEdit().setPlaceholderText("Selecione ou digite")
        self.block_search_input.lineEdit().setClearButtonEnabled(False)
        self.block_search_input.lineEdit().returnPressed.connect(self.handle_block_search)
        self.block_search_input.currentIndexChanged.connect(self._handle_block_search_selection)
        self.block_search_clear_button = QToolButton(search_widget)
        self.block_search_clear_button.setObjectName("toolbarSearchClear")
        self.block_search_clear_button.setText("×")
        self.block_search_clear_button.setToolTip("Limpar a seleção de bloco.")
        self.block_search_clear_button.clicked.connect(self._clear_block_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.block_search_input)
        search_layout.addWidget(self.block_search_clear_button)
        toolbar.addWidget(search_widget)

        toolbar.addAction(result_action)
        self._style_toolbar_button(session_button, "menu", session_button.toolTip(), 92)
        self._style_toolbar_button(toolbar.widgetForAction(save_action), "primary", save_action.toolTip(), 84)
        self._style_toolbar_button(toolbar.widgetForAction(share_session_action), "quiet", share_session_action.toolTip(), 112)
        self._style_toolbar_button(toolbar.widgetForAction(fill_page_action), "quiet", fill_page_action.toolTip(), 96)
        self._style_toolbar_button(toolbar.widgetForAction(result_action), "accent", result_action.toolTip(), 102)

    def _style_toolbar_button(self, button, tone: str, tooltip: str, min_width: int | None = None) -> None:
        if button is None:
            return
        button.setProperty("toolbarTone", tone)
        button.setToolTip(tooltip)
        if min_width is not None:
            button.setMinimumWidth(min_width)
        button.style().unpolish(button)
        button.style().polish(button)

    def _build_layout(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        self.splitter = splitter

        left_group = QGroupBox("Lançamentos", self)
        left_group.setObjectName("launchPanel")
        left_group.setMinimumWidth(520)
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(12, 10, 12, 12)
        left_layout.setSpacing(8)
        launch_filters = QWidget(left_group)
        launch_filters.setObjectName("launchFiltersBar")
        launch_filters_layout = QHBoxLayout(launch_filters)
        launch_filters_layout.setContentsMargins(0, 0, 0, 2)
        launch_filters_layout.setSpacing(6)

        self.launch_filter_group = QButtonGroup(self)
        self.launch_filter_group.setExclusive(True)
        self.launch_filter_buttons: dict[str, QToolButton] = {}
        for label, key, tooltip in (
            ("Todos", "all", "Mostrar todos os blocos e páginas."),
            ("Atual", "current", "Focar apenas o bloco e a página atuais."),
            ("Premiados", "awarded", "Ver somente blocos e páginas com prêmio."),
            ("Pendentes", "pending", "Ver apenas o que ainda pede ação."),
        ):
            button = QToolButton(launch_filters)
            button.setText(label)
            button.setCheckable(True)
            button.setProperty("launchFilter", True)
            button.setToolTip(tooltip)
            button.clicked.connect(lambda checked=False, mode=key: self._set_launch_filter(mode))
            self.launch_filter_group.addButton(button)
            self.launch_filter_buttons[key] = button
            launch_filters_layout.addWidget(button)

        launch_filters_layout.addStretch(1)
        self.launch_compact_button = QToolButton(launch_filters)
        self.launch_compact_button.setText("Compacto")
        self.launch_compact_button.setCheckable(True)
        self.launch_compact_button.setProperty("launchCompact", True)
        self.launch_compact_button.setToolTip("Reduzir a altura das linhas para operação rápida.")
        self.launch_compact_button.toggled.connect(self._set_launch_compact_mode)
        launch_filters_layout.addWidget(self.launch_compact_button)

        self.launch_filter_buttons["all"].setChecked(True)
        left_layout.addWidget(launch_filters)
        left_layout.addWidget(self.bets_view)

        middle_group = QWidget(self)
        middle_group.setObjectName("middlePanel")
        middle_group.setMinimumWidth(390)
        middle_layout = QVBoxLayout(middle_group)
        middle_layout.setContentsMargins(2, 0, 2, 0)
        middle_layout.setSpacing(6)
        middle_layout.addWidget(self.result_panel, 0)
        middle_layout.addWidget(self.overview_panel, 6)
        middle_layout.addWidget(self.pending_panel, 3)

        right_group = QGroupBox("Financeiro", self)
        right_group.setObjectName("financePanel")
        right_group.setMinimumWidth(520)
        right_layout = QVBoxLayout(right_group)
        right_layout.setContentsMargins(12, 10, 12, 12)
        right_layout.setSpacing(8)
        right_layout.addWidget(self.finance_view, 1)
        right_layout.addWidget(self.finance_totals_panel, 0)

        splitter.addWidget(left_group)
        splitter.addWidget(middle_group)
        splitter.addWidget(right_group)
        splitter.setStretchFactor(0, 19)
        splitter.setStretchFactor(1, 12)
        splitter.setStretchFactor(2, 19)
        splitter.setSizes([600, 380, 600])

        container = QWidget(self)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(10, 6, 10, 10)
        container_layout.setSpacing(0)
        container_layout.addWidget(splitter)
        self.setCentralWidget(container)

    def refresh_panels(self) -> None:
        self.result_panel.set_result(self.controller.state.result)
        self.overview_panel.set_data(self.controller.get_session_overview_data())
        self.pending_panel.set_data(self.controller.get_operational_pendencies())
        self.bottom_bar.set_data(self.controller.get_bottom_bar_data())
        self.finance_totals_panel.set_data(self.controller.get_finance_totals_data())
        self._refresh_block_search_options()
        self.update_window_clock()

    def _set_launch_filter(self, filter_mode: str) -> None:
        self.bets_model.set_filter_mode(filter_mode)
        for key, button in self.launch_filter_buttons.items():
            button.blockSignals(True)
            button.setChecked(key == filter_mode)
            button.blockSignals(False)
        self._restore_launch_focus_after_filter()

    def _set_launch_compact_mode(self, enabled: bool) -> None:
        self.bets_view.set_compact_mode(enabled)

    def _restore_launch_focus_after_filter(self) -> None:
        state = self.controller.state.ui_state
        target_index = None

        if state.selected_line_id:
            for row_index in range(self.bets_model.rowCount()):
                if self.bets_model.line_id_for_row(row_index) == state.selected_line_id:
                    column = state.selected_column if state.selected_column in (0, 1) else 0
                    target_index = self.bets_model.index(row_index, column)
                    break

        if target_index is None and state.selected_page_id:
            row_index = self.bets_model.page_header_row(state.selected_page_id)
            if row_index is None:
                row_index = self.bets_model.action_row_for_page(state.selected_page_id)
            if row_index is None:
                row_index = self.bets_model.first_editable_row_for_page(state.selected_page_id)
            if row_index is not None:
                target_index = self.bets_model.index(row_index, 0)

        if target_index is None and state.selected_block_id:
            row_index = self.bets_model.block_header_row(state.selected_block_id)
            if row_index is not None:
                target_index = self.bets_model.index(row_index, 0)

        if target_index is None:
            for row_index in range(self.bets_model.rowCount()):
                row = self.bets_model.row_at(row_index)
                if row.row_type in {RowType.BLOCK_HEADER, RowType.PAGE_HEADER, RowType.BET_ENTRY}:
                    target_index = self.bets_model.index(row_index, 0)
                    break

        if target_index is None or not target_index.isValid():
            return
        self.bets_view.setCurrentIndex(target_index)
        self.bets_view.scrollTo(target_index)

    def _refresh_block_search_options(self) -> None:
        line_edit = self.block_search_input.lineEdit() if hasattr(self, "block_search_input") else None
        current_text = line_edit.text().strip() if line_edit is not None else ""
        block_numbers = [row.block_number for row in self.controller.get_finance_rows()]
        self._syncing_block_search = True
        self.block_search_input.blockSignals(True)
        self.block_search_input.clear()
        if block_numbers:
            self.block_search_input.addItems(block_numbers)
        self.block_search_input.setCurrentText(current_text)
        self.block_search_input.blockSignals(False)
        self._syncing_block_search = False

    def _select_all_in_block_search(self) -> None:
        line_edit = self.block_search_input.lineEdit()
        if line_edit is not None:
            line_edit.selectAll()

    def _clear_block_search(self) -> None:
        line_edit = self.block_search_input.lineEdit()
        self._syncing_block_search = True
        self.block_search_input.blockSignals(True)
        self.block_search_input.setCurrentIndex(-1)
        if line_edit is not None:
            line_edit.clear()
            line_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.block_search_input.blockSignals(False)
        self._syncing_block_search = False

    def _handle_block_search_selection(self, index: int) -> None:
        if self._syncing_block_search or index < 0:
            return
        self._navigate_to_block_number(self.block_search_input.itemText(index))

    def _navigate_to_block_number(self, raw_value: str) -> bool:
        digits = "".join(character for character in raw_value.strip() if character.isdigit())
        if not digits:
            self.statusBar().showMessage("Informe um número de bloco válido.", 4000)
            self._select_all_in_block_search()
            return False

        target_number = digits.zfill(3)
        row = next((item for item in self.controller.get_finance_rows() if item.block_number == target_number), None)
        if row is None:
            self.statusBar().showMessage(f"Bloco {target_number} não encontrado.", 4000)
            self._select_all_in_block_search()
            return False

        self.handle_focus_block(row.block_id)
        self.statusBar().showMessage(f"Bloco {target_number} localizado.", 4000)
        self._syncing_block_search = True
        self.block_search_input.setCurrentText(target_number)
        self._syncing_block_search = False
        self._select_all_in_block_search()
        return True

    def _active_protected_line_ids(self) -> set[str]:
        editing_line_id = self.bets_view.editing_line_id()
        return {editing_line_id} if editing_line_id else set()

    def _ensure_mobile_backend_running(self):
        if self.mobile_backend_manager is None:
            return None
        return self.mobile_backend_manager.ensure_running()

    def _show_mobile_backend_startup_feedback(self) -> None:
        result = self._startup_mobile_backend_result
        if result is None or result.running or not result.message:
            return
        self.statusBar().showMessage(result.message, 8000)

    def _blank_session_ui_state(self) -> UiState:
        return UiState(
            geometry=base64.b64encode(bytes(self.saveGeometry())).decode("ascii"),
            window_state=base64.b64encode(bytes(self.saveState())).decode("ascii"),
            splitter_state=base64.b64encode(bytes(self.splitter.saveState())).decode("ascii"),
            selected_block_id=None,
            selected_page_id=None,
            selected_line_id=None,
            selected_column=0,
        )

    def _confirm_session_replacement(self, action_text: str) -> bool:
        if not self.controller.has_meaningful_session():
            return True
        return ask_confirmation(
            self,
            "Trocar sessão",
            (
                f"A sessão atual será substituída ao {action_text}.\n\n"
                "Deseja continuar?"
            ),
        )

    def _maybe_offer_runtime_resume(self) -> None:
        if self.controller.has_meaningful_session() or not self.controller.has_resumable_active_session():
            return
        should_restore = ask_confirmation(
            self,
            "Retomar sessão em andamento",
            (
                "Foi encontrada uma sessão temporária em andamento.\n\n"
                "Deseja retomar essa sessão agora?"
            ),
        )
        if should_restore:
            try:
                if self.controller.restore_active_session():
                    self._restore_ui_state()
                    self._restore_initial_focus()
                    session_name = self.controller.state.session_name or "Sessão ativa"
                    self.statusBar().showMessage(f"Sessão retomada: {session_name}", 5000)
            except Exception as exc:  # noqa: BLE001
                self.show_error(str(exc))
            return
        self.controller.discard_active_runtime_session()
        self.statusBar().showMessage("Sessão temporária descartada.", 5000)

    def sync_external_mobile_values(self) -> None:
        protected_line_ids = set()
        editing_line_id = self.bets_view.editing_line_id()
        if editing_line_id:
            protected_line_ids.add(editing_line_id)

        protected_finance_block_ids = set()
        editing_block_id = self.finance_view.editing_block_id()
        if editing_block_id:
            protected_finance_block_ids.add(editing_block_id)

        result = self.controller.sync_external_mobile_values_if_needed(protected_line_ids)
        refresh_block_ids = set(result.block_ids)
        blocked_finance_updates = refresh_block_ids & protected_finance_block_ids
        if blocked_finance_updates:
            self._pending_finance_refresh_block_ids.update(blocked_finance_updates)
        refresh_block_ids -= protected_finance_block_ids

        pending_ready_blocks = {
            block_id
            for block_id in self._pending_finance_refresh_block_ids
            if block_id not in protected_finance_block_ids
        }
        if pending_ready_blocks:
            refresh_block_ids.update(pending_ready_blocks)
            self._pending_finance_refresh_block_ids.difference_update(pending_ready_blocks)

        if result.has_changes:
            self.bets_model.refresh_external_values(result.line_ids, result.page_ids)
            self.refresh_panels()
        if refresh_block_ids:
            self.finance_model.refresh_blocks(refresh_block_ids)

    def _restore_initial_focus(self) -> None:
        selected_line_id = self.controller.state.ui_state.selected_line_id
        if selected_line_id:
            self.bets_view.focus_line(selected_line_id)
            return
        if self.bets_model.rowCount() == 0:
            return
        for row_index in range(self.bets_model.rowCount()):
            row = self.bets_model.row_at(row_index)
            if row.row_type == RowType.BET_ENTRY:
                index = self.bets_model.index(row_index, 0)
                self.bets_view.setCurrentIndex(index)
                self.bets_view.edit(index)
                break

    def _page_is_really_empty(self, page) -> bool:
        return all(
            line.is_empty
            and not line.is_valid_bet
            and not line.is_error
            and line.value is None
            and not line.winners
            and not (line.raw_text or "").strip()
            for line in page.lines
        )

    def _cleanup_previous_block_trailing_empty_page(self) -> None:
        blocks = self.controller.state.blocks
        if not blocks:
            return
        previous_block = blocks[-1]
        if len(previous_block.pages) <= 1:
            return
        if previous_block.money_locked:
            return
        last_page = previous_block.pages[-1]
        if not self._page_is_really_empty(last_page):
            return
        self.controller.delete_page(last_page.page_id)

    def handle_create_block(self) -> None:
        dialog = BlockDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.value():
            return
        try:
            self._cleanup_previous_block_trailing_empty_page()
            block_id, page_id, _line_id = self.controller.create_block(dialog.value())
            self.handle_focus_block(block_id)
            self.bets_view.focus_page_entry(page_id, column=0, start_edit=True)
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_create_page(self, page_id: str) -> None:
        try:
            _, line_id = self.controller.create_page_after(page_id)
            self.bets_view.focus_line(line_id)
        except (PageLockedError, BlockLockedError) as exc:
            self.handle_locked_action(exc, lambda: self._create_page_force(page_id))
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def _create_page_force(self, page_id: str) -> None:
        _, line_id = self.controller.create_page_after(page_id, force_unlock=True)
        self.bets_view.focus_line(line_id)

    def handle_result_dialog(self) -> None:
        dialog = ResultDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.controller.set_result(dialog.values())
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_apply_page_value(self) -> None:
        page_id = self.controller.state.ui_state.selected_page_id
        if not page_id:
            self.show_error("Escolha uma página antes de preencher.")
            return
        page_info = find_page(self.controller.state.blocks, page_id)
        if page_info is None:
            self.show_error("Página não encontrada.")
            return
        block, page = page_info
        dialog = ValueDialog(
            "Preencher página",
            "Valor",
            self,
            description=(
                f"Você vai preencher os valores do bloco {block.number} - Pág. {page.number}.\n"
                "O valor informado será aplicado a todas as apostas editáveis desta página."
            ),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.controller.apply_value_to_page(page_id, dialog.value())
        except (PageLockedError, BlockLockedError) as exc:
            self.handle_locked_action(exc, lambda: self._apply_page_value_force(page_id, dialog.value()))
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def _apply_page_value_force(self, page_id: str, value_text: str) -> None:
        self.controller.apply_value_to_page(page_id, value_text, force_unlock=True)

    def handle_total_paid_prizes_change(self, value_text: str) -> None:
        try:
            self.controller.set_total_paid_prizes(
                value_text,
                protected_line_ids=self._active_protected_line_ids(),
            )
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_session_notes_change(self, text: str) -> None:
        try:
            self.controller.set_session_notes(
                text,
                protected_line_ids=self._active_protected_line_ids(),
            )
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_locked_action(self, exception, callback) -> None:
        title = "Página bloqueada" if isinstance(exception, PageLockedError) else "Bloco bloqueado"
        if ask_confirmation(self, title, f"{exception}\n\nDeseja desbloquear agora?"):
            try:
                callback()
            except Exception as exc:  # noqa: BLE001
                self.show_error(str(exc))

    def handle_delete_page(self, page_id: str) -> None:
        if not ask_confirmation(self, "Excluir página", "Deseja excluir a página selecionada?"):
            return
        try:
            target_page = self.controller.delete_page(page_id)
            if target_page:
                row_index = self.bets_model.first_editable_row_for_page(target_page)
                if row_index is not None:
                    index = self.bets_model.index(row_index, 0)
                    self.bets_view.setCurrentIndex(index)
                    self.bets_view.edit(index)
        except (PageLockedError, BlockLockedError) as exc:
            self.handle_locked_action(exc, lambda: self._delete_page_force(page_id))
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def _delete_page_force(self, page_id: str) -> None:
        self.controller.delete_page(page_id, force_unlock=True)

    def handle_delete_block(self, block_id: str) -> None:
        if not ask_confirmation(self, "Excluir bloco", "Deseja excluir o bloco selecionado?"):
            return
        try:
            self.controller.delete_block(block_id)
        except (PageLockedError, BlockLockedError) as exc:
            self.handle_locked_action(exc, lambda: self.controller.delete_block(block_id, force_unlock=True))
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_save(self) -> None:
        self._capture_ui_state()
        path = self.controller.save_session(protected_line_ids=self._active_protected_line_ids())
        self.statusBar().showMessage(f"Sessão salva: {path.name}", 5000)

    def handle_open(self) -> None:
        dialog = self.build_open_file_dialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected_files = dialog.selectedFiles()
        if not selected_files:
            return
        path = selected_files[0]
        if not self._confirm_session_replacement("abrir uma sessão salva"):
            return
        try:
            self.controller.load_session(Path(path))
            self._restore_ui_state()
            self._restore_initial_focus()
            self.statusBar().showMessage(f"Sessão aberta: {Path(path).name}", 5000)
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def build_open_file_dialog(self) -> QFileDialog:
        dialog = QFileDialog(self, "Abrir sessão salva", str(self.root / "saves"), "Arquivos JSON (*.json)")
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setNameFilter("Arquivos JSON (*.json)")
        return dialog

    def handle_new_session(self) -> None:
        if not self._confirm_session_replacement("abrir uma nova sessão"):
            return
        try:
            self.controller.start_new_session(ui_state=self._blank_session_ui_state())
            self._restore_initial_focus()
            self.statusBar().showMessage("Nova sessão pronta para uso.", 5000)
            self.handle_session_name()
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_end_session(self) -> None:
        has_runtime = self.controller.has_active_runtime_session()
        has_session = self.controller.has_meaningful_session()
        if not has_runtime and not has_session:
            self.statusBar().showMessage("Não há sessão aberta para encerrar.", 5000)
            return
        if has_session and not ask_confirmation(
            self,
            "Encerrar sessão",
            (
                "A sessão atual será salva e encerrada.\n\n"
                "Deseja continuar?"
            ),
        ):
            return
        try:
            save_path = self.controller.end_session(
                protected_line_ids=self._active_protected_line_ids(),
                ui_state=self._blank_session_ui_state(),
            )
            self._restore_initial_focus()
            if save_path is not None:
                self.statusBar().showMessage(
                    f"Sessão encerrada e salva: {save_path.name}",
                    5000,
                )
            else:
                self.statusBar().showMessage("Sessão encerrada.", 5000)
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_session_name(self) -> None:
        dialog = SessionNameDialog(self.controller.state.session_name, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.controller.set_session_name(
                dialog.value(),
                protected_line_ids=self._active_protected_line_ids(),
            )
            display_name = self.controller.state.session_name or "Sessão ativa"
            self.statusBar().showMessage(f"Nome da sessão: {display_name}", 5000)
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_share_session(self) -> None:
        host = detect_local_network_ip()
        if host is None:
            self.show_error("Não foi possível detectar um IP válido da rede local para compartilhar a sessão.")
            return

        url = build_mobile_share_url(host, DEFAULT_MOBILE_PORT)
        backend_ready = is_mobile_backend_reachable(host, DEFAULT_MOBILE_PORT)
        backend_result = None
        if not backend_ready:
            backend_result = self._ensure_mobile_backend_running()
            backend_ready = is_mobile_backend_reachable(host, DEFAULT_MOBILE_PORT)
        if not backend_ready:
            startup_message = backend_result.message if backend_result is not None else ""
            prompt_text = (
                "O backend mobile não respondeu no endereço abaixo.\n\n"
                f"{url}\n\n"
            )
            if startup_message:
                prompt_text = f"{startup_message}\n\n{prompt_text}"
            should_copy_anyway = ask_confirmation(
                self,
                "Backend mobile indisponível",
                f"{prompt_text}Deseja copiar o link mesmo assim?",
            )
            if not should_copy_anyway:
                self.statusBar().showMessage("Compartilhamento cancelado.", 5000)
                return

        clipboard = QApplication.clipboard()
        if clipboard is None:
            self.show_error("Não foi possível acessar a área de transferência.")
            return
        clipboard.setText(url)
        if backend_ready:
            self.statusBar().showMessage(f"Link da sessão copiado: {url}", 6000)
            return
        self.statusBar().showMessage(f"Link copiado: {url}", 6000)

    def handle_whatsapp_config(self, block_id: str) -> None:
        row = next((item for item in self.controller.get_finance_rows() if item.block_id == block_id), None)
        dialog = WhatsAppDialog(row.whatsapp_phone if row else None, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.controller.set_block_whatsapp(block_id, dialog.value())

    def handle_whatsapp_send(self, block_id: str) -> None:
        row = next((item for item in self.controller.get_finance_rows() if item.block_id == block_id), None)
        if row is None or not row.whatsapp_phone:
            self.show_error("O bloco n\u00e3o possui WhatsApp configurado.")
            return
        try:
            self.whatsapp_service.open_message(row.whatsapp_phone, self.controller.build_whatsapp_message(block_id))
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_contact_menu(self, block_id: str, global_pos) -> None:
        row = next((item for item in self.controller.get_finance_rows() if item.block_id == block_id), None)
        if self._contact_menu is not None:
            self._contact_menu.close()
            self._contact_menu.deleteLater()
        menu = QMenu(self)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        config_action = menu.addAction("Configurar contato / WhatsApp")
        send_action = menu.addAction("Enviar para o número")
        send_action.setEnabled(bool(row and row.whatsapp_phone))
        config_action.triggered.connect(lambda checked=False, target=block_id: self.handle_whatsapp_config(target))
        send_action.triggered.connect(lambda checked=False, target=block_id: self.handle_whatsapp_send(target))
        menu.aboutToHide.connect(self._clear_contact_menu)
        self._contact_menu = menu
        menu.popup(global_pos)

    def handle_focus_block(self, block_id: str) -> None:
        try:
            self.controller.focus_block(block_id)
            if self.bets_model.block_header_row(block_id) is None:
                self._set_launch_filter("all")
            self.bets_view.focus_block(block_id, column=0, start_edit=False)
            self.bets_view.flash_block(block_id)
            self.finance_view.focus_block(block_id)
            block = next((item for item in self.controller.state.blocks if item.block_id == block_id), None)
            if block is not None:
                self._syncing_block_search = True
                self.block_search_input.setCurrentText(block.number)
                self._syncing_block_search = False
        except Exception as exc:  # noqa: BLE001
            self.show_error(str(exc))

    def handle_bottom_block_selected(self, block_id: str) -> None:
        self.handle_focus_block(block_id)

    def handle_block_search(self) -> None:
        line_edit = self.block_search_input.lineEdit()
        raw_value = (line_edit.text() if line_edit is not None else self.block_search_input.currentText()).strip()
        self._navigate_to_block_number(raw_value)

    def _clear_contact_menu(self) -> None:
        self._contact_menu = None

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, APP_NAME, message)

    def update_window_clock(self) -> None:
        clock_text = datetime.now().strftime("%H:%M")
        session_name = (self.controller.state.session_name or "").strip()
        if session_name:
            context_text = session_name
        elif self.controller.has_meaningful_session():
            context_text = "Sessão em andamento"
        else:
            context_text = "Sem sessão aberta"
        self.title_label.setText(APP_NAME)
        self.title_meta_label.setText(f"{context_text} • {clock_text}")
        self.setWindowTitle(f"{APP_NAME} - {context_text}")

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            return
        self.showFullScreen()

    def _capture_ui_state(self) -> None:
        ui_state = UiState(
            geometry=base64.b64encode(bytes(self.saveGeometry())).decode("ascii"),
            window_state=base64.b64encode(bytes(self.saveState())).decode("ascii"),
            splitter_state=base64.b64encode(bytes(self.splitter.saveState())).decode("ascii"),
            selected_block_id=self.controller.state.ui_state.selected_block_id,
            selected_page_id=self.controller.state.ui_state.selected_page_id,
            selected_line_id=self.controller.state.ui_state.selected_line_id,
            selected_column=self.controller.state.ui_state.selected_column,
        )
        self.controller.set_ui_state(ui_state)

    def _restore_ui_state(self) -> None:
        ui_state = self.controller.state.ui_state
        if ui_state.geometry:
            self.restoreGeometry(base64.b64decode(ui_state.geometry))
        if ui_state.window_state:
            self.restoreState(base64.b64decode(ui_state.window_state))
        if ui_state.splitter_state:
            self.splitter.restoreState(base64.b64decode(ui_state.splitter_state))
