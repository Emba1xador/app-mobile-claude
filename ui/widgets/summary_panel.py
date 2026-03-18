from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGroupBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget


class SummaryPanel(QGroupBox):
    def __init__(self, title: str = "Confer\u00eancia", parent=None) -> None:
        super().__init__(title, parent)
        self.setObjectName("summaryPanel")
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.container = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(5)
        self.container_layout.addStretch(1)
        self.scroll_area.setWidget(self.container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 7)
        layout.setSpacing(0)
        layout.addWidget(self.scroll_area)

    def set_lines(self, summary_lines) -> None:
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for index, line in enumerate(summary_lines):
            is_pending_panel = self.objectName() == "pendingPanel"
            row_widget = QWidget(self.container)
            row_widget.setProperty("summaryRow", True)
            row_widget.setProperty("summaryKind", line.kind)
            row_widget.setProperty("summaryTone", line.tone)
            row_widget.setProperty("summaryLead", index == 0)
            row_layout = QHBoxLayout(row_widget)
            if line.kind == "section":
                top_margin = 5
                bottom_margin = 3
                indent_step = 18 if not is_pending_panel else 17
            else:
                top_margin = 2 if not is_pending_panel else 1
                bottom_margin = 1 if not is_pending_panel else 1
                indent_step = 17 if not is_pending_panel else 16
            row_layout.setContentsMargins(6 + (line.indent * indent_step), top_margin, 6, bottom_margin)
            row_layout.setSpacing(3)
            label = QLabel(line.text, row_widget)
            label.setWordWrap(True)
            label.setProperty("summaryTone", line.tone)
            label.setProperty("summaryKind", line.kind)
            label.setProperty("summaryLead", index == 0)
            row_layout.addWidget(label)
            self.container_layout.insertWidget(self.container_layout.count() - 1, row_widget)
