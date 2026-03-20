from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
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
    return "1 pág" if count == 1 else f"{count} pág"


def _bet_label(count: int) -> str:
    return "1 aposta" if count == 1 else f"{count} apostas"


def _prize_label(count: int) -> str:
    return "1 prêmio" if count == 1 else f"{count} prêmios"


class BlockRowWidget(QWidget):
    """Custom painted block row for session overview — crisp and cohesive."""

    clicked = Signal()

    def __init__(self, text: str, is_selected: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.text = text
        self.is_selected = is_selected
        self._hovered = False
        self.setMinimumHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = self.rect()
        row_rect = rect.adjusted(2, 2, -2, -2)

        # Background — transparent by default, visible on select/hover
        if self.is_selected:
            fill = QColor(192, 120, 24, 40)
        elif self._hovered:
            fill = QColor(255, 255, 255, 12)
        else:
            fill = QColor(0, 0, 0, 0)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(row_rect, 6, 6)

        # Bottom separator
        if not self.is_selected:
            painter.setPen(QPen(QColor(255, 255, 255, 16), 0.5))
            painter.drawLine(row_rect.left() + 8, int(row_rect.bottom()), int(row_rect.right() - 8), int(row_rect.bottom()))

        # Text
        font = QFont(painter.font())
        font.setPointSizeF(9.6)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(224, 220, 212) if self.is_selected else QColor(208, 204, 196))
        text_rect = row_rect.adjusted(10, 0, -8, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)

        painter.end()


class AwardedBlockWidget(QWidget):
    """Custom painted awarded block row — green accent."""

    clicked = Signal()
    toggled = Signal(bool)

    def __init__(self, text: str, is_selected: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.text = text
        self.is_selected = is_selected
        self._hovered = False
        self._expanded = False
        self.setMinimumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self.update()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()

    def mousePressEvent(self, event) -> None:
        self._expanded = not self._expanded
        self.toggled.emit(self._expanded)
        self.clicked.emit()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = self.rect()
        row_rect = rect.adjusted(2, 1, -2, -1)

        # Subtle bg on hover
        if self._hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 10))
            painter.drawRoundedRect(row_rect, 4, 4)

        # Left accent bar — green
        bar_rect = QRectF(row_rect.left() + 4, row_rect.top() + 8, 3, row_rect.height() - 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(60, 200, 100))
        painter.drawRoundedRect(bar_rect, 1.5, 1.5)

        # Arrow — small triangle
        arrow_font = QFont(painter.font())
        arrow_font.setPointSizeF(7.5)
        arrow_font.setBold(True)
        painter.setFont(arrow_font)
        painter.setPen(QColor(60, 200, 100))
        arrow_rect = QRectF(row_rect.left() + 14, row_rect.top(), 14, row_rect.height())
        painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "\u25be" if self._expanded else "\u25b8")

        # Text
        font = QFont(painter.font())
        font.setPointSizeF(9.3)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(100, 220, 140))
        text_rect = QRectF(row_rect.left() + 30, row_rect.top(), row_rect.width() - 38, row_rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)

        # Bottom separator
        painter.setPen(QPen(QColor(255, 255, 255, 12), 0.5))
        painter.drawLine(int(row_rect.left()) + 10, int(row_rect.bottom()), int(row_rect.right()) - 6, int(row_rect.bottom()))

        painter.end()


class SessionOverviewPanel(QGroupBox):
    blockNavigationRequested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Resumo da sessão", parent)
        self.setObjectName("sessionOverviewPanel")
        self._result_loaded: bool | None = None
        self._selected_block_id = ""
        self._expanded_awarded_block_ids: set[str] = set()
        self._current_awarded_blocks: list[dict] = []

        self.tab_buttons: list[QToolButton] = []
        self.tab_bar_widget = QWidget(self)
        tab_layout = QHBoxLayout(self.tab_bar_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(6)
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

        self.copy_awarded_button = QToolButton(self.tab_bar_widget)
        self.copy_awarded_button.setText("Copiar")
        self.copy_awarded_button.setProperty("launchCompact", True)
        self.copy_awarded_button.setToolTip("Copiar lista de premiados formatada para WhatsApp.")
        self.copy_awarded_button.clicked.connect(self._copy_awarded_to_clipboard)
        self.copy_awarded_button.setVisible(False)
        tab_layout.addWidget(self.copy_awarded_button)

        self.stack = QStackedWidget(self)
        self.blocks_page, self.blocks_layout = self._build_page("overviewBlocksPage")
        self.awarded_page, self.awarded_layout = self._build_page("overviewAwardedPage")
        self.stack.addWidget(self.blocks_page)
        self.stack.addWidget(self.awarded_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
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

        self._current_awarded_blocks = list(data.get("awarded_blocks", []))
        self._render_blocks(list(data.get("blocks", [])))
        self._render_awarded_blocks(
            self._current_awarded_blocks,
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
        layout.setSpacing(4)
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
            self.blocks_layout.insertWidget(0, self._build_empty_state("Nenhum bloco nesta sessão."))
            return

        for block in blocks:
            row_widget = BlockRowWidget(
                text=self._block_row_text(block),
                is_selected=str(block["block_id"]) == self._selected_block_id,
                parent=self.blocks_page,
            )
            block_id = str(block["block_id"])
            row_widget.clicked.connect(lambda bid=block_id: self.blockNavigationRequested.emit(bid))
            self.blocks_layout.insertWidget(self.blocks_layout.count() - 1, row_widget)

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
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(3)

            header = AwardedBlockWidget(
                text=(
                    f"Bloco {block['block_number']} \u2022 {_page_label(int(block['page_count']))} \u2022 "
                    f"{_prize_label(int(block['prize_count']))}"
                ),
                is_selected=block_id == self._selected_block_id,
                parent=container,
            )
            header.set_expanded(block_id in self._expanded_awarded_block_ids)

            details_widget = QWidget(container)
            details_widget.setVisible(block_id in self._expanded_awarded_block_ids)
            details_layout = QVBoxLayout(details_widget)
            details_layout.setContentsMargins(20, 2, 4, 6)
            details_layout.setSpacing(4)

            for detail in block["details"]:
                detail_row = QWidget(details_widget)
                detail_row.setProperty("overviewDetailRow", True)
                detail_row_layout = QVBoxLayout(detail_row)
                detail_row_layout.setContentsMargins(10, 6, 10, 6)
                detail_row_layout.setSpacing(2)

                bet_label = QLabel(str(detail["bet_text"]), detail_row)
                bet_label.setProperty("overviewDetailBet", True)
                detail_row_layout.addWidget(bet_label)

                meta_label = QLabel(
                    (
                        f"Pág. {detail['page_number']} \u2022 Linha {detail['line_number']} \u2022 "
                        f"{str(detail['text']).split(' \u2022 ')[-1]}"
                    ),
                    detail_row,
                )
                meta_label.setProperty("overviewDetailMeta", True)
                meta_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                detail_row_layout.addWidget(meta_label)
                details_layout.addWidget(detail_row)

            def _toggle_details(checked: bool, *, block_key=block_id, panel=details_widget, hdr=header) -> None:
                panel.setVisible(checked)
                hdr.set_expanded(checked)
                if checked:
                    self._expanded_awarded_block_ids.add(block_key)
                else:
                    self._expanded_awarded_block_ids.discard(block_key)

            header.clicked.connect(lambda bid=block_id: self.blockNavigationRequested.emit(bid))
            header.toggled.connect(_toggle_details)
            container_layout.addWidget(header)
            container_layout.addWidget(details_widget)
            self.awarded_layout.insertWidget(self.awarded_layout.count() - 1, container)

    def _copy_awarded_to_clipboard(self) -> None:
        if not self._current_awarded_blocks:
            QApplication.clipboard().setText("🏆 *Premiados*\n\nNenhum bloco premiado.")
            return
        lines = ["\U0001f3c6 *Premiados*"]
        for block in self._current_awarded_blocks:
            block_num = block.get("block_number", "???")
            page_count = int(block.get("page_count", 0))
            prize_count = int(block.get("prize_count", 0))
            lines.append(f"\n*Bloco {block_num}* \u2022 {_page_label(page_count)} \u2022 {_prize_label(prize_count)}")
            for detail in block.get("details", []):
                bet_text = str(detail.get("bet_text", ""))
                page_number = detail.get("page_number", "?")
                line_number = detail.get("line_number", "?")
                lines.append(f"  - {bet_text} (Pág. {page_number} \u2022 Linha {line_number})")
        QApplication.clipboard().setText("\n".join(lines))

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
        self.copy_awarded_button.setVisible(index == 1)
