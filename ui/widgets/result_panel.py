from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QGroupBox, QSizePolicy, QVBoxLayout, QWidget


class ResultRow(QWidget):
    """Single prize row — custom painted for crisp visuals."""

    def __init__(self, position: int, parent=None) -> None:
        super().__init__(parent)
        self.position = position
        self.milhar = "\u2014"
        self.group_text = "Grupo --"
        self.is_first = position == 1
        self.setMinimumHeight(44 if self.is_first else 38)

    def set_data(self, milhar: str, group_text: str) -> None:
        self.milhar = milhar
        self.group_text = group_text
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = QRectF(self.rect())
        row_rect = QRectF(rect.left() + 4, rect.top() + 2, rect.width() - 8, rect.height() - 4)

        # Clean background — slate overlay
        if self.is_first:
            fill = QColor(255, 255, 255, 12)
        else:
            fill = QColor(255, 255, 255, 7)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(row_rect, 6, 6)

        inner_left = row_rect.left() + 12
        inner_right = row_rect.right() - 12

        # Prize label — "1° prêmio"
        prize_font = QFont(painter.font())
        prize_font.setPointSizeF(8.0)
        prize_font.setWeight(QFont.Weight.Bold)
        painter.setFont(prize_font)
        painter.setPen(QColor(138, 136, 128))  # text_muted
        prize_text = f"{self.position}\u00ba prêmio"
        prize_w = QFontMetrics(prize_font).horizontalAdvance(prize_text) + 4
        prize_rect = QRectF(inner_left, row_rect.top(), prize_w, row_rect.height())
        painter.drawText(prize_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, prize_text)

        # Group label — right side
        group_font = QFont(painter.font())
        group_font.setPointSizeF(8.0)
        group_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(group_font)
        painter.setPen(QColor(102, 104, 112))  # text_subtle
        group_w = QFontMetrics(group_font).horizontalAdvance(self.group_text) + 4
        group_rect = QRectF(inner_right - group_w, row_rect.top(), group_w, row_rect.height())
        painter.drawText(group_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.group_text)

        # Milhar — CENTER, big and bold
        value_font = QFont(painter.font())
        if self.is_first:
            value_font.setPointSizeF(20.0)
        else:
            value_font.setPointSizeF(17.0)
        value_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(value_font)

        if self.milhar == "\u2014":
            painter.setPen(QColor(102, 104, 112, 120))
        else:
            painter.setPen(QColor(232, 228, 220))  # title

        value_left = inner_left + prize_w + 8
        value_right = inner_right - group_w - 8
        value_rect = QRectF(value_left, row_rect.top(), max(0, value_right - value_left), row_rect.height())
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, self.milhar)

        painter.end()


class ResultPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Resultado", parent)
        self.setObjectName("resultPanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMaximumHeight(270)
        self.result_rows: list[ResultRow] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        for position in range(1, 6):
            row = ResultRow(position, self)
            self.result_rows.append(row)
            layout.addWidget(row)

    def set_result(self, snapshot) -> None:
        if snapshot is None or not snapshot.prizes:
            for position, row in enumerate(self.result_rows, start=1):
                row.set_data("\u2014", "Grupo --")
            return
        for prize, row in zip(snapshot.prizes, self.result_rows, strict=False):
            row.set_data(prize.milhar, f"Grupo {prize.group:02d}")
