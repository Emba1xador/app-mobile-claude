"""Dialog compacto para informar o dinheiro de um bloco logo após criá-lo.

Aceita valor numérico (ex: "120,00") ou "f"/"F" para registrar como FIADO.
Enter confirma · Escape cancela.
"""
from __future__ import annotations

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QKeyEvent, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class _MoneyLineEdit(QLineEdit):
    """Campo de texto que confirma o diálogo ao pressionar Enter."""

    def __init__(self, dialog: "BlockMoneyDialog", parent=None) -> None:
        super().__init__(parent)
        self._dialog = dialog

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._dialog.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._dialog.reject()
            return
        # "f" ou "F" sozinho → registra FIADO imediatamente
        if event.key() in (Qt.Key.Key_F,) and not self.text():
            self.setText("FIADO")
            self._dialog.accept()
            return
        super().keyPressEvent(event)


class BlockMoneyDialog(QDialog):
    """Prompt rápido de dinheiro após criar um bloco.

    Uso:
        dialog = BlockMoneyDialog(block_number="042", parent=self)
        if dialog.exec() == QDialog.Accepted:
            value_text = dialog.value()   # str — número ou "FIADO" ou ""
    """

    def __init__(self, block_number: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dinheiro do bloco")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumWidth(300)
        self.setMaximumWidth(360)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QWidget(self)
        card.setObjectName("blockMoneyCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(10)

        # Header
        header = QLabel(f"Bloco <b>{block_number}</b> — quanto mandou?", card)
        header.setProperty("blockMoneyHeader", True)
        header.setWordWrap(True)
        card_layout.addWidget(header)

        # Input
        self.input = _MoneyLineEdit(self, card)
        self.input.setPlaceholderText('Valor ou "f" para FIADO')
        self.input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.input.setMinimumHeight(36)
        # Validator: dígitos, ponto, vírgula — ou "FIADO"
        # Deixamos livre para aceitar "FIADO" como string especial
        card_layout.addWidget(self.input)

        hint = QLabel('Digite o valor, ou <b>f</b> para FIADO · Enter confirma · Esc pula', card)
        hint.setProperty("blockMoneyHint", True)
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        # Buttons
        btn_row = QWidget(card)
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.addStretch(1)

        btn_skip = QPushButton("Pular", btn_row)
        btn_skip.setProperty("blockMoneySkip", True)
        btn_skip.clicked.connect(self.reject)
        btn_layout.addWidget(btn_skip)

        btn_ok = QPushButton("Confirmar", btn_row)
        btn_ok.setProperty("blockMoneyConfirm", True)
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        card_layout.addWidget(btn_row)
        outer.addWidget(card)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.input.setFocus()

    def value(self) -> str:
        return self.input.text().strip()
