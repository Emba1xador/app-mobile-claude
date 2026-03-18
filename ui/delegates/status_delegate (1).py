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
    chip_width = min(40.0 if emphasized else 34.0, rect.width())
    chip_height = min(24.0 if emphasized else 20.0, rect.height())
    chip_rect = QRectF(
        rect.left(),
        rect.center().y() - (chip_height / 2),
        chip_width,
        chip_height,
    )

    shell_fill = QColor(color("surface_alt"))
    shell_fill.setAlpha(78 if selected else 56)
    shell_border = QColor(color("divider"))
    shell_border.setAlpha(112 if selected else 72)
    painter.setPen(QPen(shell_border, 1))
    painter.setBrush(shell_fill)
    painter.drawRoundedRect(chip_rect, chip_height / 2, chip_height / 2)

    halo_rect = QRectF(
        chip_rect.left() + 6,
        chip_rect.center().y() - 6,
        12,
        12,
    )
    halo_fill = QColor(tone_color)
    halo_fill.setAlpha(58 if selected else 34)
    halo_border = QColor(tone_color)
    halo_border.setAlpha(140 if selected else 112)
    painter.setPen(QPen(halo_border, 1))
    painter.setBrush(halo_fill)
    painter.drawEllipse(halo_rect)

    dot_rect = QRectF(
        halo_rect.center().x() - 3.5,
        halo_rect.center().y() - 3.5,
        7,
        7,
    )
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(tone_color)
    painter.drawEllipse(dot_rect)

    if selected or emphasized:
        rail = QColor(tone_color)
        rail.setAlpha(210 if selected else 162)
        painter.setBrush(rail)
        painter.drawRoundedRect(
            QRectF(chip_rect.left() + 2, chip_rect.top() + 4, 2.4, chip_rect.height() - 8),
            1.2,
            1.2,
        )

    return chip_rect


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
