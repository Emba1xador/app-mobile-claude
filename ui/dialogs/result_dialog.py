from __future__ import annotations

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit


class ResultDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Inserir resultado")
        self.inputs: list[QLineEdit] = []
        self.validator = QRegularExpressionValidator(QRegularExpression(r"\d{0,4}"), self)
        layout = QFormLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(12)
        for position in range(1, 6):
            field = QLineEdit(self)
            field.setMaxLength(4)
            field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            field.setPlaceholderText("0000")
            field.setValidator(self.validator)
            field.textChanged.connect(lambda text, current=field: self._on_text_changed(current, text))
            self.inputs.append(field)
            layout.addRow(f"{position}\u00ba pr\u00eamio", field)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_button is not None:
            ok_button.setText("Salvar resultado")
        if cancel_button is not None:
            cancel_button.setText("Cancelar")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        self._update_ok_state()

    def _on_text_changed(self, current: QLineEdit, text: str) -> None:
        self._advance(current, text)
        self._update_ok_state()

    def _advance(self, current: QLineEdit, text: str) -> None:
        if len(text) != 4:
            return
        index = self.inputs.index(current)
        if index + 1 < len(self.inputs):
            self.inputs[index + 1].setFocus()
            self.inputs[index + 1].selectAll()

    def _update_ok_state(self) -> None:
        ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button is not None:
            ok_button.setEnabled(all(len(field.text()) == 4 for field in self.inputs))

    def values(self) -> list[str]:
        return [field.text().strip() for field in self.inputs]
