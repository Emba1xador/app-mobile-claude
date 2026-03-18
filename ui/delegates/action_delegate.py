from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from ui.theme import ACTION_COLORS


class ActionDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        style = option.widget.style() if option.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        text = str(index.data() or "")
        rect = QRect(option.rect.adjusted(6, 4, -6, -4))
        color = QColor(ACTION_COLORS["default"])
        if text == "\U0001f7e2":
            color = QColor(ACTION_COLORS["available"])
        elif text == "\U0001f534":
            color = QColor(ACTION_COLORS["missing"])
        elif text == "\u2699":
            color = QColor(ACTION_COLORS["config"])
        elif text == "\u279c":
            color = QColor(ACTION_COLORS["send"])

        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
