from __future__ import annotations

from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit


class BlockDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo bloco")
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Ex.: 452")
        self.input.setMaxLength(6)
        self.input.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d{1,6}"), self.input))
        layout = QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        layout.addRow("N\u00famero do bloco", self.input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText("Criar bloco")
        if cancel_button is not None:
            cancel_button.setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def value(self) -> str:
        return self.input.text().strip()
