from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit


class WhatsAppDialog(QDialog):
    def __init__(self, phone: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("WhatsApp do bloco")
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("DDD + n\u00famero")
        self.input.setText(phone or "")
        layout = QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        layout.addRow("N\u00famero", self.input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText("Salvar")
        if cancel_button is not None:
            cancel_button.setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def value(self) -> str:
        return self.input.text().strip()
