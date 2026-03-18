from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit


class ValueDialog(QDialog):
    def __init__(self, title: str, label: str, parent=None, description: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Ex.: 12,50")
        layout = QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        if description:
            description_label = QLabel(description, self)
            description_label.setWordWrap(True)
            layout.addRow(description_label)
        layout.addRow(label, self.input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText("Confirmar")
        if cancel_button is not None:
            cancel_button.setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def value(self) -> str:
        return self.input.text().strip()
