from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit


class SessionNameDialog(QDialog):
    def __init__(self, current_value: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nome da sessão")
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("Ex.: Matriz manhã")
        self.input.setText(current_value)
        self.input.selectAll()
        layout = QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        layout.addRow("Nome da sessão", self.input)
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
