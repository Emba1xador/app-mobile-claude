from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from services.formatting import format_money


class FinanceTotalsPanel(QGroupBox):
    totalPaidPrizesChanged = Signal(str)
    sessionNotesChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Resumo financeiro", parent)
        self.setObjectName("financeTotalsPanel")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._current_data: dict = {}

        self.total_received_value = self._make_value_label()
        self.total_bruto_value = self._make_value_label()
        self.total_liquido_value = self._make_value_label()
        self.total_paid_input = QLineEdit(self)
        self.total_paid_input.setProperty("totalsPaidInput", True)
        self.total_paid_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_paid_input.setPlaceholderText("0,00")
        self.total_paid_input.setMinimumHeight(24)
        self.total_paid_input.setMinimumWidth(120)

        self.cash_balance_value = QLabel(self)
        self.cash_balance_value.setProperty("totalsResult", True)
        self.cash_balance_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cash_result_value = self.cash_balance_value

        self.notes_input = QPlainTextEdit(self)
        self.notes_input.setObjectName("sessionNotes")
        self.notes_input.setPlaceholderText("Observações da sessão")
        self.notes_input.setMinimumHeight(44)
        self.notes_input.setMaximumHeight(56)
        self.notes_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(5)

        # ── Unified card: metrics + saldo ──────────────────────────────
        unified_card = QWidget(self)
        unified_card.setProperty("totalsUnifiedCard", True)
        card_layout = QVBoxLayout(unified_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Card header: title + copy button
        card_header = QWidget(unified_card)
        card_header.setProperty("totalsCardHeader", True)
        header_layout = QHBoxLayout(card_header)
        header_layout.setContentsMargins(12, 7, 10, 7)
        header_layout.setSpacing(8)

        title_lbl = QLabel("FINANCEIRO", card_header)
        title_lbl.setProperty("totalsCardTitle", True)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch(1)

        copy_button = QToolButton(card_header)
        copy_button.setText("⎘ Copiar")
        copy_button.setProperty("copyButton", True)
        copy_button.setToolTip("Copiar resumo financeiro formatado para WhatsApp.")
        copy_button.clicked.connect(self._copy_to_clipboard)
        header_layout.addWidget(copy_button)

        card_layout.addWidget(card_header)

        # Metrics rows
        metrics_body = QWidget(unified_card)
        metrics_layout = QVBoxLayout(metrics_body)
        metrics_layout.setContentsMargins(0, 4, 0, 4)
        metrics_layout.setSpacing(0)
        metrics_layout.addWidget(self._build_metric_row("Dinheiro recebido", self.total_received_value, unified_card))
        metrics_layout.addWidget(self._build_metric_row("Bruto total", self.total_bruto_value, unified_card))
        metrics_layout.addWidget(self._build_metric_row("Líquido (70%)", self.total_liquido_value, unified_card))
        metrics_layout.addWidget(self._build_metric_row("Prêmios pagos", self.total_paid_input, unified_card))
        card_layout.addWidget(metrics_body)

        # Divider
        divider = QFrame(unified_card)
        divider.setObjectName("financeTotalsDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(divider)

        # Saldo row inline (compact)
        balance_row = QWidget(unified_card)
        balance_row.setProperty("totalsBalanceRow", True)
        balance_layout = QHBoxLayout(balance_row)
        balance_layout.setContentsMargins(12, 6, 12, 8)
        balance_layout.setSpacing(8)

        balance_label = QLabel("Saldo final", balance_row)
        balance_label.setProperty("totalsBalanceLabel", True)
        balance_layout.addWidget(balance_label, 1)
        balance_layout.addWidget(self.cash_balance_value, 0)
        card_layout.addWidget(balance_row)

        layout.addWidget(unified_card)

        # ── Notes ─────────────────────────────────────────────────────
        notes_container = QWidget(self)
        notes_container.setProperty("totalsNotesGroup", True)
        notes_layout = QVBoxLayout(notes_container)
        notes_layout.setContentsMargins(2, 0, 2, 0)
        notes_layout.setSpacing(3)
        notes_label = QLabel("Observações", notes_container)
        notes_label.setProperty("totalsLabel", True)
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_input)
        layout.addWidget(notes_container, 0)

        self.total_paid_input.editingFinished.connect(self._emit_total_paid_change)
        self.notes_input.textChanged.connect(self._emit_notes_change)
        self.set_data(
            {
                "total_received": "0",
                "total_bruto": "0",
                "total_liquido": "0",
                "total_paid_prizes": "",
                "cash_balance": "0",
                "session_notes": "",
            }
        )

    def _make_value_label(self) -> QLabel:
        label = QLabel(self)
        label.setProperty("totalsMetricValue", True)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _build_metric_row(self, label_text: str, widget: QWidget, parent: QWidget) -> QWidget:
        container = QWidget(parent)
        container.setProperty("totalsMetricRow", True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel(label_text, container)
        label.setProperty("totalsMetricLabel", True)
        label.setMinimumWidth(128)
        layout.addWidget(label, 0)
        layout.addWidget(widget, 0)
        layout.addStretch(1)
        return container

    def set_data(self, data: dict[str, str | int]) -> None:
        self._current_data = dict(data)
        total_received = Decimal(str(data["total_received"]))
        total_bruto = Decimal(str(data.get("total_bruto", "0")))
        total_liquido = Decimal(str(data.get("total_liquido", "0")))
        cash_balance = Decimal(str(data.get("cash_balance", "0")))

        self.total_received_value.setText(format_money(total_received))
        self.total_bruto_value.setText(format_money(total_bruto))
        self.total_liquido_value.setText(format_money(total_liquido))

        self.total_paid_input.blockSignals(True)
        self.total_paid_input.setText(
            format_money(Decimal(str(data["total_paid_prizes"]))) if data["total_paid_prizes"] else ""
        )
        self.total_paid_input.blockSignals(False)

        if cash_balance > 0:
            display_value = f"+{format_money(cash_balance)}"
            tone = "positive"
        elif cash_balance < 0:
            display_value = format_money(cash_balance)
            tone = "negative"
        else:
            display_value = format_money(cash_balance)
            tone = "neutral"
        self.cash_balance_value.setProperty("cashTone", tone)
        self.cash_balance_value.setText(display_value)
        self.cash_balance_value.style().unpolish(self.cash_balance_value)
        self.cash_balance_value.style().polish(self.cash_balance_value)

        notes = str(data.get("session_notes") or "")
        self.notes_input.blockSignals(True)
        if self.notes_input.toPlainText() != notes:
            self.notes_input.setPlainText(notes)
        self.notes_input.blockSignals(False)

    def _copy_to_clipboard(self) -> None:
        data = self._current_data
        lines = [
            "\U0001f4ca *Resumo Financeiro*",
            f"Dinheiro recebido: R$ {format_money(Decimal(str(data.get('total_received', '0'))))}",
            f"Bruto total: R$ {format_money(Decimal(str(data.get('total_bruto', '0'))))}",
            f"Líquido (70%): R$ {format_money(Decimal(str(data.get('total_liquido', '0'))))}",
        ]
        if data.get("total_paid_prizes"):
            lines.append(f"Prêmios pagos: R$ {format_money(Decimal(str(data['total_paid_prizes'])))}")
        balance = Decimal(str(data.get("cash_balance", "0")))
        sign = "+" if balance > 0 else ""
        lines.append(f"*Saldo final: R$ {sign}{format_money(balance)}*")
        QApplication.clipboard().setText("\n".join(lines))

    def _emit_total_paid_change(self) -> None:
        self.totalPaidPrizesChanged.emit(self.total_paid_input.text().strip())

    def _emit_notes_change(self) -> None:
        self.sessionNotesChanged.emit(self.notes_input.toPlainText())
