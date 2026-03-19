from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


def _issue_count_label(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular}" if count == 1 else f"{count} {plural}"


class PendencyHeaderWidget(QWidget):
    """Custom painted pendency group header."""

    def __init__(self, text: str, tone: str = "warning", parent=None) -> None:
        super().__init__(parent)
        self.text = text
        self.tone = tone
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
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = QRectF(self.rect().adjusted(2, 1, -2, -1))
        is_critical = self.tone == "critical"

        # Subtle bg on hover
        if self._hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 8))
            painter.drawRoundedRect(rect, 4, 4)

        # Left accent bar — amber for critical, muted for normal
        bar_color = QColor(192, 130, 16) if is_critical else QColor(160, 152, 136)
        bar_rect = QRectF(rect.left() + 4, rect.top() + 8, 3, rect.height() - 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        painter.drawRoundedRect(bar_rect, 1.5, 1.5)

        # Arrow — small
        arrow_font = QFont(painter.font())
        arrow_font.setPointSizeF(7.5)
        arrow_font.setBold(True)
        painter.setFont(arrow_font)
        arrow_color = QColor(192, 130, 16) if is_critical else QColor(122, 114, 100)
        painter.setPen(arrow_color)
        arrow_rect = QRectF(rect.left() + 14, rect.top(), 14, rect.height())
        painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "\u25be" if self._expanded else "\u25b8")

        # Text
        font = QFont(painter.font())
        font.setPointSizeF(9.3)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        text_color = QColor(108, 72, 8) if is_critical else QColor(58, 52, 40)
        painter.setPen(text_color)
        text_rect = QRectF(rect.left() + 30, rect.top(), rect.width() - 38, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)

        # Bottom separator
        painter.setPen(QPen(QColor(0, 0, 0, 12), 0.5))
        painter.drawLine(int(rect.left()) + 10, int(rect.bottom()), int(rect.right()) - 6, int(rect.bottom()))

        painter.end()


class PendencyPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Pendências do horário", parent)
        self.setObjectName("pendingPanel")
        self._expanded_group_ids: set[str] = set()

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(4)
        self.container_layout.addStretch(1)
        self.scroll_area.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(0)
        layout.addWidget(self.scroll_area)

    def set_data(self, data: dict[str, object]) -> None:
        self._clear()

        groups = list(data.get("groups", []))
        valid_group_ids = {str(group["group_id"]) for group in groups}
        self._expanded_group_ids &= valid_group_ids

        if not groups:
            message = str(data.get("ready_message") or "Horário pronto para fechamento.")
            self.container_layout.insertWidget(0, self._build_empty_state(message))
            return

        for group in groups:
            group_id = str(group["group_id"])
            tone = str(group.get("tone") or "warning")

            container = QWidget(self.container)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            header = PendencyHeaderWidget(
                text=self._summary_text(group),
                tone=tone,
                parent=container,
            )
            header.set_expanded(group_id in self._expanded_group_ids)

            details_widget = QWidget(container)
            details_widget.setProperty("pendencyDetails", True)
            details_widget.setVisible(group_id in self._expanded_group_ids)
            details_layout = QVBoxLayout(details_widget)
            details_layout.setContentsMargins(24, 2, 4, 6)
            details_layout.setSpacing(3)

            for item_text in group.get("items", []):
                detail = QLabel(str(item_text), details_widget)
                detail.setWordWrap(True)
                detail.setProperty("pendencyDetail", True)
                detail.setProperty("pendencyTone", tone)
                details_layout.addWidget(detail)

            def _toggle(checked: bool, *, group_key=group_id, panel=details_widget, hdr=header) -> None:
                panel.setVisible(checked)
                hdr.set_expanded(checked)
                if checked:
                    self._expanded_group_ids.add(group_key)
                else:
                    self._expanded_group_ids.discard(group_key)

            header.mousePressEvent = lambda event, cb=_toggle, h=header: (
                h.__class__.mousePressEvent(h, event),
                cb(h._expanded),
            )

            container_layout.addWidget(header)
            container_layout.addWidget(details_widget)
            self.container_layout.insertWidget(self.container_layout.count() - 1, container)

    def _summary_text(self, group: dict[str, object]) -> str:
        title = str(group.get("title") or "Pendência")
        parts: list[str] = []
        critical_count = int(group.get("critical_count") or 0)
        warning_count = int(group.get("warning_count") or 0)
        total_count = int(group.get("total_count") or 0)

        if critical_count:
            parts.append(_issue_count_label(critical_count, "crítica", "críticas"))
        if warning_count:
            parts.append(_issue_count_label(warning_count, "aviso", "avisos"))
        if not critical_count and not warning_count and total_count:
            parts.append(_issue_count_label(total_count, "pendência", "pendências"))

        suffix = " \u2022 ".join(parts)
        return f"{title} \u2022 {suffix}" if suffix else title

    def _clear(self) -> None:
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _build_empty_state(self, text: str) -> QLabel:
        label = QLabel(text, self.container)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setProperty("pendencyEmpty", True)
        label.setMinimumHeight(62)
        return label
