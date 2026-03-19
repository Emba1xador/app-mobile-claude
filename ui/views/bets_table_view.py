from __future__ import annotations

import logging

from PySide6.QtCore import QEvent, QItemSelection, QItemSelectionModel, QModelIndex, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPen, QShortcut
from PySide6.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QHeaderView, QMenu, QTableView

from core.enums import BetType, CommitMode, Flag, RowType
from core.page_lock import BlockLockedError, PageLockedError
from services.commands import SelectionContext
from ui.delegates.bet_delegate import BetDelegate
from ui.delegates.value_delegate import ValueDelegate
from ui.theme import color, tinted

LOGGER = logging.getLogger(__name__)


class BetsTableView(QTableView):
    createBlockRequested = Signal()
    createPageRequested = Signal(str)
    deletePageRequested = Signal(str)
    deleteBlockRequested = Signal(str)
    renameBlockRequested = Signal(str)   # block_id
    lockConflict = Signal(object, object)

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.compact_mode = False
        self._flash_block_id: str | None = None
        self._flash_clear_timer = QTimer(self)
        self._flash_clear_timer.setSingleShot(True)
        self._flash_clear_timer.timeout.connect(self._clear_block_flash)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(46)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.viewport().installEventFilter(self)
        self._ctrl_up_shortcut = QShortcut("Ctrl+Up", self)
        self._ctrl_down_shortcut = QShortcut("Ctrl+Down", self)
        self._ctrl_up_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._ctrl_down_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._ctrl_up_shortcut.activated.connect(lambda: self.extend_selection("up"))
        self._ctrl_down_shortcut.activated.connect(lambda: self.extend_selection("down"))
        self._selection_anchor_row: int | None = None

    def setModel(self, model) -> None:  # noqa: N802
        super().setModel(model)
        self.setItemDelegateForColumn(0, BetDelegate(self))
        self.setItemDelegateForColumn(1, ValueDelegate(self))
        self.selectionModel().selectionChanged.connect(self._selection_changed)
        model.modelReset.connect(self._apply_spans)
        self._apply_spans()

    def set_compact_mode(self, enabled: bool) -> None:
        self.compact_mode = enabled
        self.verticalHeader().setDefaultSectionSize(36 if enabled else 46)
        self.resizeRowsToContents()
        self.doItemsLayout()
        self.viewport().update()

    def flash_block(self, block_id: str, duration_ms: int = 900) -> None:
        self._flash_block_id = block_id
        self.viewport().update()
        self._flash_clear_timer.start(duration_ms)

    def _clear_block_flash(self) -> None:
        if self._flash_block_id is None:
            return
        self._flash_block_id = None
        self.viewport().update()

    def _apply_spans(self) -> None:
        self.clearSpans()
        model = self.model()
        if model is None:
            return
        for row_index in range(model.rowCount()):
            row = model.row_at(row_index)
            if row.row_type in {RowType.BLOCK_HEADER, RowType.PAGE_HEADER}:
                self.setSpan(row_index, 0, 1, 2)
        self.resizeRowsToContents()

    def _selection_changed(self, selected, deselected) -> None:
        del selected, deselected
        index = self.currentIndex()
        if not index.isValid():
            return
        row = self.model().row_at(index.row())
        if row.row_type == RowType.BLOCK_HEADER:
            return
        self.controller.update_selection(
            SelectionContext(
                block_id=row.block_id,
                page_id=row.page_id or None,
                line_id=row.line_id,
                column=index.column(),
            )
        )

    def current_line_ids(self) -> list[str]:
        ids: list[str] = []
        for index in self.selectionModel().selectedRows():
            line_id = self.model().line_id_for_row(index.row())
            if line_id:
                ids.append(line_id)
        return ids

    def eventFilter(self, watched, event) -> bool:
        if watched is self.viewport() and event.type() == QEvent.Type.KeyPress:
            if self._handle_key_event(event):
                return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            row = self.model().row_at(index.row())
            if row.row_type == RowType.BLOCK_HEADER:
                block_id = row.block_id
                self.model().toggle_block_expansion(block_id)
                header_row = self.model().block_header_row(block_id)
                if header_row is not None:
                    header_index = self.model().index(header_row, 0)
                    self.setCurrentIndex(header_index)
                    QTimer.singleShot(0, lambda idx=header_index: self.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop))
                event.accept()
                return
            if row.row_type == RowType.PAGE_HEADER:
                self.focus_page_action(row.page_id)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            row = self.model().row_at(index.row())
            if row.row_type == RowType.BLOCK_HEADER:
                self.model().ensure_block_expanded(row.block_id)
                target_row = self.model().first_pending_editable_row_for_block(row.block_id, column=0)
                if target_row is not None:
                    target_index = self.model().index(target_row, 0)
                    self.setCurrentIndex(target_index)
                    self.scrollTo(target_index)
                    self.edit(target_index)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event) -> None:
        if self._handle_key_event(event):
            return
        self._selection_anchor_row = None
        super().keyPressEvent(event)

    def _handle_key_event(self, event) -> bool:
        index = self.currentIndex()
        if not index.isValid():
            return False
        if event.modifiers() & Qt.ControlModifier and event.key() in (Qt.Key_Up, Qt.Key_Down):
            self.extend_selection("up" if event.key() == Qt.Key_Up else "down")
            event.accept()
            return True
        if event.key() == Qt.Key_B and not event.modifiers():
            self.createBlockRequested.emit()
            event.accept()
            return True
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.state() != QAbstractItemView.EditingState:
            row = self.model().row_at(index.row())
            if row.row_type == RowType.BLOCK_HEADER:
                block_id = row.block_id
                self.model().toggle_block_expansion(block_id)
                header_row = self.model().block_header_row(block_id)
                if header_row is not None:
                    header_index = self.model().index(header_row, 0)
                    self.setCurrentIndex(header_index)
                    QTimer.singleShot(0, lambda idx=header_index: self.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop))
                return True
            if row.row_type == RowType.PAGE_HEADER:
                self.focus_page_action(row.page_id)
                return True
            self.activate_current_cell()
            event.accept()
            return True
        if event.key() == Qt.Key_Shift and self.current_line_ids():
            self.toggle_mc()
            event.accept()
            return True
        if index.column() == 0 and self._is_numpad_comma(event):
            self.createPageRequested.emit(self.model().page_id_for_row(index.row()))
            event.accept()
            return True
        if index.column() == 0:
            if self._is_numpad_key(event, Qt.Key_Minus):
                self.apply_flag(Flag.INVERTIDA)
                event.accept()
                return True
            if self._is_numpad_key(event, Qt.Key_Plus):
                self.apply_flag(Flag.DE)
                event.accept()
                return True
            if self._is_numpad_key(event, Qt.Key_Asterisk):
                self.apply_flag(Flag.DEM)
                event.accept()
                return True
        return False

    def edit_current(self) -> None:
        index = self.currentIndex()
        if index.isValid():
            self.edit(index)

    def commit_bet_editor(self, editor, direction: str, commit_mode) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        payload = {"text": editor.text(), "commit_mode": commit_mode}
        if self.model().setData(index, payload, Qt.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda: self._move_after_commit(index, direction, column=0))
        else:
            exc = self.model().last_exception
            if isinstance(exc, (PageLockedError, BlockLockedError)):
                self.lockConflict.emit(exc, lambda: self.retry_commit(index, payload, editor, direction))
                return
            editor.selectAll()

    def retry_commit(self, index: QModelIndex, payload: dict, editor, direction: str) -> None:
        payload = dict(payload)
        payload["force_unlock"] = True
        if self.model().setData(index, payload, Qt.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda: self._move_after_commit(index, direction, column=0))
        else:
            editor.selectAll()

    def commit_value_editor(self, editor, direction: str) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        payload = {"text": editor.text()}
        if self.model().setData(index, payload, Qt.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda: self._move_after_commit(index, direction, column=1))
        else:
            exc = self.model().last_exception
            if isinstance(exc, (PageLockedError, BlockLockedError)):
                self.lockConflict.emit(exc, lambda: self.retry_value_commit(index, payload, editor, direction))
                return
            editor.selectAll()

    def retry_value_commit(self, index: QModelIndex, payload: dict, editor, direction: str) -> None:
        payload = dict(payload)
        payload["force_unlock"] = True
        if self.model().setData(index, payload, Qt.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda: self._move_after_commit(index, direction, column=1))
        else:
            editor.selectAll()

    def handle_editor_action(self, index: QModelIndex, action: str, editor) -> None:
        if action == "new_page":
            self.createPageRequested.emit(self.model().page_id_for_row(index.row()))
            return
        if action == "new_block":
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            self.createBlockRequested.emit()
            return
        if action == "extend_up":
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            self.extend_selection("up")
            return
        if action == "extend_down":
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            self.extend_selection("down")
            return
        if action == "flag_iv":
            self.apply_flag_from_editor(editor, Flag.INVERTIDA)
            return
        if action == "flag_de":
            self.apply_flag_from_editor(editor, Flag.DE)
            return
        if action == "flag_dem":
            self.apply_flag_from_editor(editor, Flag.DEM)

    def _move_after_commit(self, index: QModelIndex, direction: str, column: int) -> None:
        row = index.row()
        if direction == "up":
            target = self._previous_editable_row(row, column)
        else:
            target = self._next_editable_row(row, column)
        if column == 1 and direction != "up" and target is None:
            self.setCurrentIndex(index)
            self.scrollTo(index)
            return
        if target is None:
            target = row
        next_index = self.model().index(target, column)
        self.setCurrentIndex(next_index)
        self.scrollTo(next_index)
        if column == 1 and self.model().row_at(target).is_trailing_blank:
            return
        self.edit(next_index)

    def _next_editable_row(self, current_row: int, column: int = 0) -> int | None:
        for row in range(current_row + 1, self.model().rowCount()):
            projection = self.model().row_at(row)
            if projection.row_type != RowType.BET_ENTRY:
                continue
            if column == 1 and projection.is_trailing_blank:
                continue
            return row
        return None

    def _previous_editable_row(self, current_row: int, column: int = 0) -> int | None:
        for row in range(current_row - 1, -1, -1):
            projection = self.model().row_at(row)
            if projection.row_type != RowType.BET_ENTRY:
                continue
            if column == 1 and projection.is_trailing_blank:
                continue
            return row
        return None

    def open_context_menu(self, point: QPoint) -> None:
        index = self.indexAt(point)
        if not self.prepare_context_selection(index):
            return
        row = self.model().row_at(index.row())
        menu, actions, transform_actions, flag_actions, clear_flags_action = self._build_context_menu(row)
        selected = menu.exec(self.viewport().mapToGlobal(point))
        if selected == actions["insert_above"]:
            self._context_action(
                lambda: self.controller.insert_line_above(row.line_id),
                lambda: self.controller.insert_line_above(row.line_id, force_unlock=True),
            )
        elif selected == actions["insert_below"]:
            self._context_action(
                lambda: self.controller.insert_line_below(row.line_id),
                lambda: self.controller.insert_line_below(row.line_id, force_unlock=True),
            )
        elif selected == actions["new_page"]:
            self.createPageRequested.emit(row.page_id)
        elif selected == actions["new_block"]:
            self.createBlockRequested.emit()
        elif selected == actions["toggle_mc"]:
            self.toggle_mc()
        elif selected == actions["delete_line"]:
            self._context_action(
                lambda: self.controller.delete_line(row.line_id),
                lambda: self.controller.delete_line(row.line_id, force_unlock=True),
            )
        elif selected == actions["delete_page"]:
            self.deletePageRequested.emit(row.page_id)
        elif selected == actions["delete_block"]:
            self.deleteBlockRequested.emit(row.block_id)
        elif selected == actions.get("rename_block"):
            self.renameBlockRequested.emit(row.block_id)
        elif selected in transform_actions:
            self.transform_selection(transform_actions[selected])
        elif selected in flag_actions:
            self.apply_flag(flag_actions[selected], mode="add")
        elif selected == clear_flags_action:
            self.clear_flags()

    def _build_context_menu(self, row):
        menu = QMenu(self)
        actions = {
            "insert_above": menu.addAction("Inserir acima"),
            "insert_below": menu.addAction("Inserir abaixo"),
            "new_page": menu.addAction("Nova página"),
            "new_block": menu.addAction("Novo bloco"),
        }
        menu.addSeparator()
        transform_menu = menu.addMenu("Transformar")
        transform_actions = {
            transform_menu.addAction("Centena (C)"): BetType.CENTENA,
            transform_menu.addAction("Milhar (M)"): BetType.MILHAR,
            transform_menu.addAction("Milhar/centena (MC)"): BetType.MILHAR_CENTENA,
            transform_menu.addAction("Dezena (D)"): BetType.DEZENA,
            transform_menu.addAction("Duque de dezena (DD)"): BetType.DUQUE_DEZENA,
            transform_menu.addAction("Terno de dezena (TD)"): BetType.TERNO_DEZENA,
            transform_menu.addAction("Grupo (G)"): BetType.GRUPO,
            transform_menu.addAction("Terno de grupo (TG)"): BetType.TERNO_GRUPO,
            transform_menu.addAction("Fechamento (F)"): BetType.FECHAMENTO,
        }
        actions["toggle_mc"] = menu.addAction("Alternar MC")
        menu.addSeparator()
        flags_menu = menu.addMenu("Flags")
        flag_actions = {
            flags_menu.addAction("Marcar I.V."): Flag.INVERTIDA,
            flags_menu.addAction("Marcar DE"): Flag.DE,
            flags_menu.addAction("Marcar DEM"): Flag.DEM,
        }
        flags_menu.addSeparator()
        clear_flags_action = flags_menu.addAction("Limpar flags")
        menu.addSeparator()
        actions["rename_block"] = menu.addAction("Alterar número do bloco")
        menu.addSeparator()
        actions["delete_line"] = menu.addAction("Excluir linha")
        actions["delete_page"] = menu.addAction("Excluir página")
        actions["delete_block"] = menu.addAction("Excluir bloco")
        return menu, actions, transform_actions, flag_actions, clear_flags_action

    def _context_action(self, callback, force_callback) -> None:
        try:
            self._run_context_action(callback)
        except (PageLockedError, BlockLockedError) as exc:
            self.lockConflict.emit(exc, lambda: self._run_context_action(force_callback))

    def _run_context_action(self, callback) -> None:
        line_id = callback()
        if line_id:
            self.focus_line(line_id)

    def focus_page_action(self, page_id: str) -> None:
        self.focus_page_entry(page_id, column=0, start_edit=True)

    def focus_page_entry(self, page_id: str, column: int = 0, start_edit: bool = True) -> bool:
        model = self.model()
        block_id = next(
            (
                block.block_id
                for block in self.controller.state.blocks
                if any(page.page_id == page_id for page in block.pages)
            ),
            None,
        )
        if block_id is not None:
            model.ensure_block_expanded(block_id)

        header_row = model.page_header_row(page_id)
        target_row = model.first_editable_row_for_page(page_id)
        if target_row is None:
            target_row = model.action_row_for_page(page_id)
        if target_row is None:
            return False

        target_index = model.index(target_row, column)
        self.setCurrentIndex(target_index)
        self.selectionModel().select(
            target_index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
        )

        if header_row is not None:
            header_index = model.index(header_row, 0)
            self.scrollTo(header_index, QAbstractItemView.ScrollHint.PositionAtTop)
            header_rect = self.visualRect(header_index)
            if header_rect.isValid() and header_rect.top() > 6:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() + header_rect.top() - 6)
            self.scrollTo(target_index, QAbstractItemView.ScrollHint.EnsureVisible)
        else:
            self.scrollTo(target_index, QAbstractItemView.ScrollHint.PositionAtTop)

        if start_edit and not (column == 1 and model.row_at(target_row).is_trailing_blank):
            self.edit(target_index)
        return True

    def focus_line(self, line_id: str, start_edit: bool = True, column: int = 0) -> None:
        for row_index in range(self.model().rowCount()):
            if self.model().line_id_for_row(row_index) == line_id:
                index = self.model().index(row_index, column)
                self.setCurrentIndex(index)
                self.scrollTo(index)
                if start_edit and not (column == 1 and self.model().row_at(row_index).is_trailing_blank):
                    self.edit(index)
                break

    def focus_block(self, block_id: str, column: int = 0, start_edit: bool = False) -> None:
        self.model().ensure_block_expanded(block_id)
        if start_edit:
            row_index = self.model().first_pending_editable_row_for_block(block_id, column=column)
        else:
            row_index = self.model().first_header_row_for_block(block_id)
        if row_index is None:
            return
        index = self.model().index(row_index, column)
        self.setCurrentIndex(index)
        self.selectionModel().select(
            index,
            QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
        )
        self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtTop)
        rect = self.visualRect(index)
        if rect.isValid() and rect.top() > 0:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + rect.top())
        if start_edit and not (column == 1 and self.model().row_at(row_index).is_trailing_blank):
            self.edit(index)

    def editing_line_id(self) -> str | None:
        if self.state() != QAbstractItemView.State.EditingState:
            return None
        index = self.currentIndex()
        if not index.isValid():
            return None
        return self.model().line_id_for_row(index.row())

    def apply_flag(self, flag, mode: str = "toggle") -> None:
        line_ids = self.current_line_ids()
        if not line_ids:
            return
        current_line_id = self.model().line_id_for_row(self.currentIndex().row()) if self.currentIndex().isValid() else None
        try:
            changed = self.controller.apply_flag(line_ids, flag, mode=mode)
        except (PageLockedError, BlockLockedError) as exc:
            self.lockConflict.emit(
                exc,
                lambda: self._apply_flag_with_restore(line_ids, current_line_id, flag, mode, force_unlock=True),
            )
        except Exception:
            LOGGER.exception("Erro inesperado ao aplicar flag")
        else:
            if changed:
                QTimer.singleShot(0, lambda: self._focus_next_line_after_flag(current_line_id))

    def _apply_flag_with_restore(self, line_ids: list[str], current_line_id: str | None, flag, mode: str, force_unlock: bool = False) -> None:
        changed = self.controller.apply_flag(line_ids, flag, mode=mode, force_unlock=force_unlock)
        if changed:
            QTimer.singleShot(0, lambda: self._focus_next_line_after_flag(current_line_id))

    def apply_flag_from_editor(self, editor, flag) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        flagged_text = self.controller.resolve_flag_input(editor.text(), flag, mode="toggle", commit_mode=CommitMode.ENTER)
        if not flagged_text:
            editor.end(False)
            return
        payload = {"text": flagged_text, "commit_mode": CommitMode.ENTER}
        if self.model().setData(index, payload, Qt.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.NoHint)
            QTimer.singleShot(0, lambda: self._move_after_commit(index, "next", column=0))
            return
        exc = self.model().last_exception
        if isinstance(exc, (PageLockedError, BlockLockedError)):
            self.lockConflict.emit(exc, lambda: self.retry_commit(index, payload, editor, "next"))
            return
        editor.selectAll()

    def clear_flags(self) -> None:
        line_ids = self.current_line_ids()
        if not line_ids:
            return
        try:
            self.controller.clear_flags(line_ids)
        except (PageLockedError, BlockLockedError) as exc:
            self.lockConflict.emit(exc, lambda: self.controller.clear_flags(line_ids, force_unlock=True))

    def transform_selection(self, target_type: BetType) -> None:
        line_ids = self.current_line_ids()
        if not line_ids:
            return
        try:
            self.controller.transform_lines(line_ids, target_type)
        except (PageLockedError, BlockLockedError) as exc:
            self.lockConflict.emit(
                exc,
                lambda: self.controller.transform_lines(line_ids, target_type, force_unlock=True),
            )

    def toggle_mc(self) -> None:
        line_ids = self.current_line_ids()
        if not line_ids:
            return
        try:
            self.controller.toggle_mc(line_ids)
        except (PageLockedError, BlockLockedError) as exc:
            self.lockConflict.emit(exc, lambda: self.controller.toggle_mc(line_ids, force_unlock=True))

    def activate_current_cell(self) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        row = self.model().row_at(index.row())
        if row.row_type == RowType.PAGE_HEADER:
            self.focus_page_action(row.page_id)
            return
        if row.row_type == RowType.BLOCK_HEADER:
            block_id = row.block_id
            self.model().toggle_block_expansion(block_id)
            header_row = self.model().block_header_row(block_id)
            if header_row is not None:
                header_index = self.model().index(header_row, 0)
                self.setCurrentIndex(header_index)
                QTimer.singleShot(0, lambda idx=header_index: self.scrollTo(idx, QAbstractItemView.ScrollHint.PositionAtTop))
            return
        if index.column() == 1 and row.is_trailing_blank:
            target_row = self._next_editable_row(index.row(), column=1)
            if target_row is None:
                return
            target_index = self.model().index(target_row, 1)
            self.setCurrentIndex(target_index)
            self.scrollTo(target_index)
            self.edit(target_index)
            return
        self.edit(index)

    def _focus_next_line_after_flag(self, current_line_id: str | None) -> None:
        if current_line_id is None:
            return
        current_row = None
        for row_index in range(self.model().rowCount()):
            if self.model().line_id_for_row(row_index) == current_line_id:
                current_row = row_index
                break
        if current_row is None:
            return
        target_row = self._next_editable_row(current_row, column=0)
        if target_row is None:
            self.focus_line(current_line_id, start_edit=False, column=0)
            return
        target_index = self.model().index(target_row, 0)
        self.setCurrentIndex(target_index)
        self.scrollTo(target_index)
        self.edit(target_index)

    def extend_selection(self, direction: str) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        if self._selection_anchor_row is None:
            self._selection_anchor_row = index.row()
        target_row = self._previous_editable_row(index.row(), index.column()) if direction == "up" else self._next_editable_row(index.row(), index.column())
        if target_row is None:
            return
        self._apply_range_selection(self._selection_anchor_row, target_row, index.column())

    def _apply_range_selection(self, anchor_row: int, target_row: int, column: int) -> None:
        selection_model = self.selectionModel()
        start = min(anchor_row, target_row)
        end = max(anchor_row, target_row)
        selection = QItemSelection(self.model().index(start, column), self.model().index(end, column))
        selection_model.select(
            selection,
            QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
        )
        current_index = self.model().index(target_row, column)
        selection_model.setCurrentIndex(current_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        self.scrollTo(current_index)

    def prepare_context_selection(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        row = self.model().row_at(index.row())
        if row.row_type != RowType.BET_ENTRY or row.line_id is None:
            return False
        selection_model = self.selectionModel()
        if not selection_model.isRowSelected(index.row(), QModelIndex()):
            selection_model.select(
                index,
                QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
            )
        selection_model.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.NoUpdate)
        return True

    def _is_numpad_key(self, event, key) -> bool:
        return bool(event.modifiers() & Qt.KeypadModifier) and event.key() == key

    def _is_numpad_comma(self, event) -> bool:
        return bool(event.modifiers() & Qt.KeypadModifier) and event.key() in {Qt.Key_Comma, Qt.Key_Period}
