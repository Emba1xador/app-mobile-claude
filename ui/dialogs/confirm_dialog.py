from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def ask_confirmation(parent: QWidget, title: str, text: str) -> bool:
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Question)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    yes_button = dialog.addButton("Sim", QMessageBox.ButtonRole.YesRole)
    no_button = dialog.addButton("N\u00e3o", QMessageBox.ButtonRole.NoRole)
    dialog.setDefaultButton(no_button)
    dialog.setEscapeButton(no_button)
    dialog.exec()
    return dialog.clickedButton() is yes_button
