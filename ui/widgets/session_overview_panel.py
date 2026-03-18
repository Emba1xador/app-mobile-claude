from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def _page_label(count: int) -> str:
    return "1 p\u00e1g" if count == 1 else f"{count} p\u00e1g"


def _bet_label(count: int) -> str:
    return "1 aposta" if count == 1 else f"{count} apostas"


def _prize_label(count: int) -> str:
    return "1 pr\u00eamio" if count == 1 else f"{count} pr\u00eamios"


class SessionOverviewPanel(QGroupBox):
    blockNavigationRequested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Resumo da sess\u00e3o", parent)
        self.setObjectName("sessionOverviewPanel")
        self._result_loaded: bool | None = None
        self._selected_block_id = ""
        self._expanded_awarded_block_ids: set[str] = set()

        self.tab_buttons: list[QToolButton] = []
        self.tab_bar_widget = QWidget(self)
        tab_layout = QHBoxLayout(self.tab_bar_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(10)
        for index, label in enumerate(("Blocos", "Premiados")):
            button = QToolButton(self.tab_bar_widget)
            button.setCheckable(True)
            button.setAutoRaise(False)
            button.setText(label)
            button.setProperty("overviewTab", True)
            button.clicked.connect(lambda checked=False, target=index: self._set_tab(target))
            tab_layout.addWidget(button)
            self.tab_buttons.append(button)
        tab_layout.addStretch(1)

        self.stack = QStackedWidget(self)
        self.blocks_page, self.blocks_layout = self._build_page("overviewBlocksPage")
        self.awarded_page, self.awarded_layout = self._build_page("overviewAwardedPage")
        self.stack.addWidget(self.blocks_page)
        self.stack.addWidget(self.awarded_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(8)
        layout.addWidget(self.tab_bar_widget)
        layout.addWidget(self.stack, 1)

        self._set_tab(0)

    def current_tab_key(self) -> str:
        return "awarded" if self.stack.currentIndex() == 1 else "blocks"

    def set_data(self, data: dict[str, object]) -> None:
        result_loaded = bool(data.get("result_loaded"))
        self._selected_block_id = str(data.get("selected_block_id") or "")
        if self._result_loaded is None:
            self._set_tab(1 if result_loaded else 0)
        elif not result_loaded:
            self._set_tab(0)
        elif not self._result_loaded and result_loaded:
            self._set_tab(1)
        self._result_loaded = result_loaded

        self._render_blocks(list(data.get("blocks", [])))
        self._render_awarded_blocks(
            list(data.get("awarded_blocks", [])),
            result_loaded=result_loaded,
        )

    def _build_page(self, object_name: str) -> tuple[QWidget, QVBoxLayout]:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName(object_name)

        container = QWidget(scroll_area)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addStretch(1)
        scroll_area.setWidget(container)
        return scroll_area, layout

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_blocks(self, blocks: list[dict[str, object]]) -> None:
        self._clear_layout(self.blocks_layout)
        if not blocks:
            self.blocks_layout.insertWidget(0, self._build_empty_state("Nenhum bloco nesta sess\u00e3o."))
            return

        for block in blocks:
            button = QToolButton(self.blocks_page)
            button.setProperty("overviewRow", True)
            button.setProperty("overviewKind", "block")
            button.setProperty("overviewSelected", str(block["block_id"]) == self._selected_block_id)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setAutoRaise(True)
            button.setText(self._block_row_text(block))
            button.setMinimumHeight(34)
            button.clicked.connect(
                lambda checked=False, block_id=str(block["block_id"]): self.blockNavigationRequested.emit(block_id)
            )
            self.blocks_layout.insertWidget(self.blocks_layout.count() - 1, button)

    def _render_awarded_blocks(self, awarded_blocks: list[dict[str, object]], *, result_loaded: bool) -> None:
        self._clear_layout(self.awarded_layout)
        if not awarded_blocks:
            empty_text = "Nenhum bloco premiado" if result_loaded else "Aguardando resultado"
            self.awarded_layout.insertWidget(0, self._build_empty_state(empty_text))
            return

        valid_block_ids = {str(block["block_id"]) for block in awarded_blocks}
        self._expanded_awarded_block_ids &= valid_block_ids

        for block in awarded_blocks:
            block_id = str(block["block_id"])
            container = QWidget(self.awarded_page)
            container.setProperty("overviewAwardedGroup", True)
            container.setProperty("overviewSelected", block_id == self._selected_block_id)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(3)

            button = QToolButton(container)
            button.setProperty("overviewRow", True)
            button.setProperty("overviewKind", "awarded")
            button.setProperty("overviewSelected", block_id == self._selected_block_id)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setArrowType(
                Qt.ArrowType.DownArrow if block_id in self._expanded_awarded_block_ids else Qt.ArrowType.RightArrow
            )
            button.setCheckable(True)
            button.setChecked(block_id in self._expanded_awarded_block_ids)
            button.setMinimumHeight(36)
            button.setText(
                f"Bloco {block['block_number']} \u2022 {_page_label(int(block['page_count']))} \u2022 "
                f"{_prize_label(int(block['prize_count']))}"
            )

            details_widget = QWidget(container)
            details_widget.setProperty("overviewDetails", True)
            details_widget.setVisible(button.isChecked())
            details_layout = QVBoxLayout(details_widget)
            details_layout.setContentsMargins(24, 0, 4, 4)
            details_layout.setSpacing(4)

            for detail in block["details"]:
                detail_row = QWidget(details_widget)
                detail_row.setProperty("overviewDetailRow", True)
                detail_row_layout = QVBoxLayout(detail_row)
                detail_row_layout.setContentsMargins(10, 5, 10, 5)
                detail_row_layout.setSpacing(2)

                bet_label = QLabel(str(detail["bet_text"]), detail_row)
                bet_label.setProperty("overviewDetailBet", True)
                detail_row_layout.addWidget(bet_label)

                meta_label = QLabel(
                    (
                        f"P\u00e1g. {detail['page_number']} \u2022 Linha {detail['line_number']} \u2022 "
                        f"{str(detail['text']).split(' \u2022 ')[-1]}"
                    ),
                    detail_row,
                )
                meta_label.setProperty("overviewDetailMeta", True)
                meta_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                detail_row_layout.addWidget(meta_label)
                details_layout.addWidget(detail_row)

            def _toggle_details(checked: bool, *, target_button=button, block_key=block_id, panel=details_widget) -> None:
                target_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
                panel.setVisible(checked)
                if checked:
                    self._expanded_awarded_block_ids.add(block_key)
                else:
                    self._expanded_awarded_block_ids.discard(block_key)

            button.clicked.connect(lambda checked=False, target=block_id: self.blockNavigationRequested.emit(target))
            button.toggled.connect(_toggle_details)
            container_layout.addWidget(button)
            container_layout.addWidget(details_widget)
            self.awarded_layout.insertWidget(self.awarded_layout.count() - 1, container)

    def _block_row_text(self, block: dict[str, object]) -> str:
        parts = [
            f"Bloco {block['block_number']}",
            _page_label(int(block["page_count"])),
            _bet_label(int(block["bet_count"])),
        ]
        state_label = str(block.get("state_label") or "").strip()
        if state_label and state_label != "ok":
            parts.append(state_label)
        return " \u2022 ".join(parts)

    def _build_empty_state(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setProperty("overviewEmpty", True)
        label.setMinimumHeight(52)
        return label

    def _set_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.tab_buttons):
            button.setChecked(button_index == index)
