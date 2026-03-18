from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from ui.delegates.status_delegate import draw_status_indicator, status_tone_color
from ui.models.finance_table_model import FinanceTableModel
from ui.theme import color


class ContactDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        style = option.widget.style() if option.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        tone = str(index.data(FinanceTableModel.CONTACT_STATE_ROLE) or "missing")
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        content_rect = QRectF(option.rect.adjusted(10, 6, -10, -6))
        chip_rect = draw_status_indicator(
            painter,
            content_rect,
            tone=tone,
            selected=selected,
            emphasized=True,
        )

        chevron_color = QColor(color("title") if selected else color("text_muted"))
        chevron_color.setAlpha(210 if selected else 168)
        painter.setPen(QPen(chevron_color, 1.8))
        center_x = min(option.rect.right() - 18, int(chip_rect.right()) + 16)
        center_y = option.rect.center().y()
        painter.drawLine(QPointF(center_x - 4.5, center_y - 2.5), QPointF(center_x, center_y + 2.2))
        painter.drawLine(QPointF(center_x, center_y + 2.2), QPointF(center_x + 4.5, center_y - 2.5))

        if selected:
            marker = QColor(status_tone_color(tone))
            marker.setAlpha(58)
            painter.setBrush(marker)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRectF(center_x - 11, center_y - 9, 20, 18),
                9,
                9,
            )
            painter.setPen(QPen(chevron_color, 1.8))
            painter.drawLine(QPointF(center_x - 4.5, center_y - 2.5), QPointF(center_x, center_y + 2.2))
            painter.drawLine(QPointF(center_x, center_y + 2.2), QPointF(center_x + 4.5, center_y - 2.5))
        painter.restore()
