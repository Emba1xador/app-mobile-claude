from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGroupBox, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout


class ResultPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Resultado", parent)
        self.setObjectName("resultPanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMaximumHeight(242)
        self.rows: list[tuple[QLabel, QLabel, QLabel]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        for position in range(1, 6):
            row = QFrame(self)
            row.setProperty("resultRow", True)
            row.setProperty("resultTopPrize", position == 1)
            row.setMinimumHeight(36)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 6, 4, 6)
            row_layout.setSpacing(14)

            prize_label = QLabel(f"{position}\u00ba pr\u00eamio", row)
            prize_label.setProperty("resultPrize", True)
            prize_label.setMinimumWidth(84)
            value_label = QLabel("\u2014", row)
            value_label.setProperty("resultValue", True)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setMinimumWidth(140)
            value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            group_label = QLabel("Grupo --", row)
            group_label.setProperty("resultGroup", True)
            group_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            group_label.setMinimumWidth(82)

            row_layout.addWidget(prize_label, 0)
            row_layout.addWidget(value_label, 2)
            row_layout.addWidget(group_label, 0)

            self.rows.append((prize_label, value_label, group_label))
            layout.addWidget(row)

    def set_result(self, snapshot) -> None:
        if snapshot is None or not snapshot.prizes:
            for position, (prize_label, value_label, group_label) in enumerate(self.rows, start=1):
                prize_label.setText(f"{position}\u00ba pr\u00eamio")
                value_label.setText("\u2014")
                group_label.setText("Grupo --")
            return
        for prize, (prize_label, value_label, group_label) in zip(snapshot.prizes, self.rows, strict=False):
            prize_label.setText(f"{prize.label} pr\u00eamio")
            value_label.setText(prize.milhar)
            group_label.setText(f"Grupo {prize.group:02d}")
