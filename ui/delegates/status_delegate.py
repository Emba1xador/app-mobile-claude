from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from ui.theme import color


def status_tone_color(tone: str) -> QColor:
    mapping = {
        "configured": color("success_detail"),
        "positive": color("success_detail"),
        "warning": color("warning_detail"),
        "missing": color("warning_detail"),
        "negative": color("danger_detail"),
        "error": color("danger_detail"),
        "neutral": color("text_muted"),
    }
    return QColor(mapping.get(tone, color("text_muted")))


def draw_status_indicator(
    painter: QPainter,
    rect: QRectF,
    *,
    tone: str,
    selected: bool = False,
    emphasized: bool = False,
) -> QRectF:
    tone_color = status_tone_color(tone)
    dot_size = 9.0 if emphasized else 7.0
    indicator_area = QRectF(
        rect.left(),
        rect.center().y() - (dot_size / 2),
        dot_size + 8,
        dot_size,
    )

    # Outer ring (subtle)
    ring_rect = QRectF(
        rect.left() + 4,
        rect.center().y() - (dot_size / 2) - 2,
        dot_size + 4,
        dot_size + 4,
    )
    ring_color = QColor(tone_color)
    ring_color.setAlpha(40 if selected else 24)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ring_color)
    painter.drawEllipse(ring_rect)

    # Solid dot
    dot_rect = QRectF(
        ring_rect.center().x() - dot_size / 2,
        ring_rect.center().y() - dot_size / 2,
        dot_size,
        dot_size,
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(tone_color)
    painter.drawEllipse(dot_rect)

    return indicator_area


class StatusDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        style = option.widget.style() if option.widget else None
        if style is not None:
            style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        tone = str(index.data() or "neutral")
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        draw_status_indicator(
            painter,
            QRectF(option.rect.adjusted(8, 6, -8, -6)),
            tone=tone,
            selected=selected,
            emphasized=True,
        )
        painter.restore()
