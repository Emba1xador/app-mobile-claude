from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QSizePolicy, QWidget

from services.formatting import format_money
from ui.theme import COLOR_TOKENS


class BottomBar(QWidget):
    blockSelected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("bottomBar")

        self.context_label = QLabel(self)
        self.context_label.setProperty("bottomContext", True)
        self.context_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.context_label.setTextFormat(Qt.TextFormat.RichText)

        self.block_selector = QComboBox(self)
        self.block_selector.setObjectName("bottomBlockSelector")
        self.block_selector.setFixedWidth(172)
        self.block_selector.setMinimumHeight(30)
        self.block_selector.setMaximumHeight(30)
        self.block_selector.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.block_selector.setToolTip("Trocar rapidamente para outro bloco.")

        self.dinheiro_label = self._make_metric_label()
        self.bruto_label = self._make_metric_label()
        self.liquido_label = self._make_metric_label()
        self.saldo_label = self._make_metric_label(strong=True)
        self.progress_label = self._make_metric_label(expanding=True)

        self.shortcuts_label = QLabel("Atalhos: B novo bloco \u2022 F9 resultado", self)
        self.shortcuts_label.setProperty("bottomHint", True)
        self.shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        context_group = self._build_context_segment()
        context_group.setProperty("bottomZone", "context")
        layout.addWidget(context_group, 0)

        metrics_group = QWidget(self)
        metrics_group.setProperty("bottomMetricsGroup", True)
        metrics_group.setProperty("bottomZone", "metrics")
        metrics_layout = QHBoxLayout(metrics_group)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(18)
        metrics_layout.addWidget(self._build_metric_segment("Dinheiro", self.dinheiro_label))
        metrics_layout.addWidget(self._build_metric_segment("Bruto", self.bruto_label))
        metrics_layout.addWidget(self._build_metric_segment("L\u00edquido", self.liquido_label))
        metrics_layout.addWidget(self._build_metric_segment("Saldo", self.saldo_label))
        metrics_layout.addWidget(self._build_metric_segment("Valores", self.progress_label), 1)
        layout.addWidget(metrics_group, 1)

        shortcuts_group = QWidget(self)
        shortcuts_group.setProperty("bottomZone", "shortcuts")
        shortcuts_layout = QHBoxLayout(shortcuts_group)
        shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_layout.setSpacing(0)
        shortcuts_layout.addWidget(self.shortcuts_label)
        layout.addWidget(shortcuts_group, 0)

        self.block_selector.currentIndexChanged.connect(self._emit_block_change)
        self.set_data(
            {
                "block": "---",
                "selected_block_id": "",
                "bruto": "0",
                "liquido": "0",
                "dinheiro": "",
                "resultado": "",
                "progress_text": "0/0",
                "blocks": [],
                "current_page": "",
            }
        )

    def _make_metric_label(self, *, strong: bool = False, expanding: bool = False) -> QLabel:
        label = QLabel("--", self)
        label.setProperty("bottomInlineValue", True)
        if strong:
            label.setProperty("bottomInlineValueStrong", True)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        if expanding:
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return label

    def _build_context_segment(self) -> QWidget:
        container = QWidget(self)
        container.setProperty("bottomSegment", True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.context_label, 0)
        layout.addWidget(self.block_selector, 0)
        return container

    def _build_metric_segment(self, title: str, value_label: QLabel) -> QWidget:
        container = QWidget(self)
        container.setProperty("bottomSegment", True)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title_label = QLabel(f"{title}:", container)
        title_label.setProperty("bottomInlineLabel", True)
        layout.addWidget(title_label, 0)
        layout.addWidget(value_label, 0)
        return container

    def _separator(self) -> QFrame:
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setProperty("bottomSeparator", True)
        return separator

    def set_data(self, data: dict[str, object]) -> None:
        block = str(data["block"])
        current_page = str(data.get("current_page") or "")
        bruto = format_money(Decimal(str(data["bruto"])))
        liquido = format_money(Decimal(str(data["liquido"])))
        recebido = format_money(Decimal(str(data["dinheiro"]))) if data["dinheiro"] else "--"
        saldo_value = None
        if data["resultado"]:
            saldo_value = Decimal(str(data["resultado"]))
            saldo = format_money(saldo_value)
            if saldo_value > 0:
                saldo = f"+{saldo}"
        else:
            saldo = "--"
        progress_text = str(data["progress_text"])

        page_suffix = f" \u2022 P\u00e1g. {current_page}" if current_page else ""
        if block == "---":
            self.context_label.setText("Sem bloco em foco")
        else:
            page_html = (
                f" <span style='color:{COLOR_TOKENS['text_muted']};'>\u2022</span> "
                f"<span style='color:{COLOR_TOKENS['text']};font-weight:700;'>P\u00e1g. {current_page}</span>"
                if current_page
                else ""
            )
            self.context_label.setText(
                f"<span style='color:{COLOR_TOKENS['title']};font-weight:700;'>Bloco {block}</span>{page_html}"
            )
        self.dinheiro_label.setText(recebido)
        self.bruto_label.setText(bruto)
        self.liquido_label.setText(liquido)
        self.saldo_label.setText(saldo)
        self.progress_label.setText(progress_text)

        saldo_tone = "neutral"
        if saldo_value is not None:
            if saldo_value > 0:
                saldo_tone = "positive"
            elif saldo_value < 0:
                saldo_tone = "negative"
        self.saldo_label.setProperty("saldoTone", saldo_tone)
        self.saldo_label.style().unpolish(self.saldo_label)
        self.saldo_label.style().polish(self.saldo_label)

        self.block_selector.blockSignals(True)
        self.block_selector.clear()
        for block_item in data.get("blocks", []):
            self.block_selector.addItem(f"Bloco {block_item['number']}", block_item["block_id"])
        target_block_id = data.get("selected_block_id", "")
        if target_block_id:
            index = self.block_selector.findData(target_block_id)
            if index >= 0:
                self.block_selector.setCurrentIndex(index)
        self.block_selector.blockSignals(False)

    def _emit_block_change(self, index: int) -> None:
        block_id = self.block_selector.itemData(index)
        if block_id:
            self.blockSelected.emit(block_id)
