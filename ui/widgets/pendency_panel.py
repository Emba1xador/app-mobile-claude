from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


def _issue_count_label(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular}" if count == 1 else f"{count} {plural}"


class PendencyPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Pend\u00eancias do hor\u00e1rio", parent)
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
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)
        layout.addWidget(self.scroll_area)

    def set_data(self, data: dict[str, object]) -> None:
        self._clear()

        groups = list(data.get("groups", []))
        valid_group_ids = {str(group["group_id"]) for group in groups}
        self._expanded_group_ids &= valid_group_ids

        if not groups:
            message = str(data.get("ready_message") or "Hor\u00e1rio pronto para fechamento.")
            self.container_layout.insertWidget(0, self._build_empty_state(message))
            return

        for group in groups:
            group_id = str(group["group_id"])
            container = QWidget(self.container)
            tone = str(group.get("tone") or "warning")
            container.setProperty("pendencyGroup", True)
            container.setProperty("pendencyTone", tone)
            container.setProperty("pendencyExpanded", group_id in self._expanded_group_ids)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            button = QToolButton(container)
            button.setCheckable(True)
            button.setChecked(group_id in self._expanded_group_ids)
            button.setArrowType(Qt.ArrowType.DownArrow if button.isChecked() else Qt.ArrowType.RightArrow)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setProperty("pendencySummaryButton", True)
            button.setProperty("pendencyTone", tone)
            button.setProperty("pendencyExpanded", button.isChecked())
            button.setText(self._summary_text(group))

            details_widget = QWidget(container)
            details_widget.setProperty("pendencyDetails", True)
            details_widget.setVisible(button.isChecked())
            details_layout = QVBoxLayout(details_widget)
            details_layout.setContentsMargins(28, 0, 4, 6)
            details_layout.setSpacing(3)

            for item_text in group.get("items", []):
                detail = QLabel(str(item_text), details_widget)
                detail.setWordWrap(True)
                detail.setProperty("pendencyDetail", True)
                detail.setProperty("pendencyTone", tone)
                details_layout.addWidget(detail)

            def _toggle(checked: bool, *, group_key=group_id, panel=details_widget, toggle_button=button) -> None:
                toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
                panel.setVisible(checked)
                if checked:
                    self._expanded_group_ids.add(group_key)
                else:
                    self._expanded_group_ids.discard(group_key)
                toggle_button.setProperty("pendencyExpanded", checked)
                container.setProperty("pendencyExpanded", checked)
                toggle_button.style().unpolish(toggle_button)
                toggle_button.style().polish(toggle_button)
                container.style().unpolish(container)
                container.style().polish(container)

            button.toggled.connect(_toggle)
            container_layout.addWidget(button)
            container_layout.addWidget(details_widget)
            self.container_layout.insertWidget(self.container_layout.count() - 1, container)

    def _summary_text(self, group: dict[str, object]) -> str:
        title = str(group.get("title") or "Pend\u00eancia")
        parts: list[str] = []
        critical_count = int(group.get("critical_count") or 0)
        warning_count = int(group.get("warning_count") or 0)
        total_count = int(group.get("total_count") or 0)

        if critical_count:
            parts.append(_issue_count_label(critical_count, "cr\u00edtica", "cr\u00edticas"))
        if warning_count:
            parts.append(_issue_count_label(warning_count, "aviso", "avisos"))
        if not critical_count and not warning_count and total_count:
            parts.append(_issue_count_label(total_count, "pend\u00eancia", "pend\u00eancias"))

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
