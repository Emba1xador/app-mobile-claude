from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
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

        self.total_received_value = self._make_value_label()
        self.total_bruto_value = self._make_value_label()
        self.total_liquido_value = self._make_value_label()
        self.total_paid_input = QLineEdit(self)
        self.total_paid_input.setProperty("totalsPaidInput", True)
        self.total_paid_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_paid_input.setPlaceholderText("0,00")
        self.total_paid_input.setMinimumHeight(32)
        self.total_paid_input.setMinimumWidth(146)

        self.cash_balance_value = QLabel(self)
        self.cash_balance_value.setProperty("totalsResult", True)
        self.cash_balance_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cash_result_value = self.cash_balance_value

        self.notes_input = QPlainTextEdit(self)
        self.notes_input.setObjectName("sessionNotes")
        self.notes_input.setPlaceholderText("Observa\u00e7\u00f5es da sess\u00e3o")
        self.notes_input.setMinimumHeight(62)
        self.notes_input.setMaximumHeight(76)
        self.notes_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)
        metrics_group = QWidget(self)
        metrics_group.setProperty("totalsMetricsGroup", True)
        metrics_layout = QVBoxLayout(metrics_group)
        metrics_layout.setContentsMargins(8, 7, 8, 7)
        metrics_layout.setSpacing(4)
        metrics_layout.addWidget(self._build_metric_row("Dinheiro recebido", self.total_received_value))
        metrics_layout.addWidget(self._build_metric_row("Bruto total", self.total_bruto_value))
        metrics_layout.addWidget(self._build_metric_row("L\u00edquido total (70%)", self.total_liquido_value))
        metrics_layout.addWidget(self._build_metric_row("Pr\u00eamios pagos", self.total_paid_input))
        layout.addWidget(metrics_group)

        divider = QFrame(self)
        divider.setObjectName("financeTotalsDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        balance_card = QWidget(self)
        balance_card.setProperty("totalsBalanceCard", True)
        balance_card.setMaximumHeight(62)
        balance_layout = QVBoxLayout(balance_card)
        balance_layout.setContentsMargins(14, 6, 14, 6)
        balance_layout.setSpacing(1)
        balance_label = QLabel("Saldo final", balance_card)
        balance_label.setProperty("totalsBalanceLabel", True)
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.cash_balance_value)
        layout.addWidget(balance_card)

        notes_container = QWidget(self)
        notes_container.setProperty("totalsNotesGroup", True)
        notes_layout = QVBoxLayout(notes_container)
        notes_layout.setContentsMargins(2, 0, 2, 0)
        notes_layout.setSpacing(4)
        notes_label = QLabel("Observa\u00e7\u00f5es", notes_container)
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

    def _build_metric_row(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget(self)
        container.setProperty("totalsMetricRow", True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel(label_text, container)
        label.setProperty("totalsMetricLabel", True)
        label.setMinimumWidth(144)
        layout.addWidget(label, 0)
        layout.addWidget(widget, 0)
        layout.addStretch(1)
        return container

    def set_data(self, data: dict[str, str | int]) -> None:
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

    def _emit_total_paid_change(self) -> None:
        self.totalPaidPrizesChanged.emit(self.total_paid_input.text().strip())

    def _emit_notes_change(self) -> None:
        self.sessionNotesChanged.emit(self.notes_input.toPlainText())
