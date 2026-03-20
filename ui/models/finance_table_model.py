from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QFont

from services.formatting import format_money
from ui.theme import color


class FinanceTableModel(QAbstractTableModel):
    CONTACT_CONFIGURED_ROLE = Qt.ItemDataRole.UserRole + 10
    CONTACT_PHONE_ROLE = Qt.ItemDataRole.UserRole + 11
    CONTACT_CAN_SEND_ROLE = Qt.ItemDataRole.UserRole + 12
    CONTACT_STATE_ROLE = Qt.ItemDataRole.UserRole + 13

    COL_CONTACT = 0
    COL_BLOCK = 1
    COL_RECEIVED = 2
    COL_BRUTO = 3
    COL_LIQUIDO = 4
    COL_SALDO = 5

    HEADERS = [
        "Status",
        "Bloco",
        "Dinheiro",
        "Bruto",
        "L\u00edquido (70%)",
        "Saldo",
    ]

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self.rows = self.controller.get_finance_rows()
        self.last_exception: Exception | None = None
        self.controller.subscribe(self.refresh)

    def refresh(self) -> None:
        self.beginResetModel()
        self.rows = self.controller.get_finance_rows()
        self.endResetModel()

    def refresh_blocks(self, block_ids: set[str]) -> None:
        if not block_ids:
            return
        refreshed_rows = {row.block_id: row for row in self.controller.get_finance_rows() if row.block_id in block_ids}
        for row_index, row in enumerate(self.rows):
            if row.block_id not in refreshed_rows:
                continue
            self.rows[row_index] = refreshed_rows[row.block_id]
            left_index = self.index(row_index, 0)
            right_index = self.index(row_index, self.columnCount() - 1)
            self.dataChanged.emit(left_index, right_index)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        return self.HEADERS[section]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]

        if index.column() == self.COL_CONTACT:
            if role == self.CONTACT_CONFIGURED_ROLE:
                return bool(row.whatsapp_phone)
            if role == self.CONTACT_PHONE_ROLE:
                return row.whatsapp_phone or ""
            if role == self.CONTACT_CAN_SEND_ROLE:
                return bool(row.whatsapp_phone)
            if role == self.CONTACT_STATE_ROLE:
                return "configured" if row.whatsapp_phone else "missing"

        if role == Qt.ItemDataRole.DisplayRole:
            match index.column():
                case self.COL_CONTACT:
                    return ""
                case self.COL_BLOCK:
                    return row.block_number
                case self.COL_RECEIVED:
                    if getattr(row, "money_fiado", False):
                        return "FIADO"
                    return "--" if row.money_received is None else format_money(row.money_received)
                case self.COL_BRUTO:
                    return format_money(row.bruto)
                case self.COL_LIQUIDO:
                    return format_money(row.liquido)
                case self.COL_SALDO:
                    return format_money(row.resultado)
        if role == Qt.ItemDataRole.EditRole and index.column() == self.COL_RECEIVED:
            return "" if row.money_received is None else format_money(row.money_received)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == self.COL_CONTACT:
                return Qt.AlignmentFlag.AlignCenter
            if index.column() == self.COL_BLOCK:
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        if role == Qt.ItemDataRole.ForegroundRole:
            if index.column() == self.COL_BLOCK:
                return QBrush(color("title"))
            if index.column() == self.COL_RECEIVED:
                if getattr(row, "money_fiado", False):
                    return QBrush(color("warning_fg"))
                token = "finance_received_missing_text" if row.money_received is None else "finance_received_text"
                return QBrush(color(token))
            if index.column() == self.COL_SALDO and row.resultado is not None:
                if row.resultado > 0:
                    return QBrush(color("success_detail"))
                if row.resultado < 0:
                    return QBrush(color("danger_detail"))
                return QBrush(color("text_muted"))
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if index.column() == self.COL_BLOCK:
                font.setPointSizeF(11.6)
                font.setBold(True)
                return font
            if index.column() == self.COL_SALDO:
                font.setPointSizeF(12.4)
                font.setBold(True)
                return font
            if index.column() == self.COL_RECEIVED and row.money_received is None:
                font.setPointSizeF(9.4)
                font.setItalic(not getattr(row, "money_fiado", False))
                font.setBold(getattr(row, "money_fiado", False))
                return font
            if index.column() in {self.COL_BRUTO, self.COL_LIQUIDO}:
                font.setPointSizeF(10.4)
                font.setBold(True)
                return font
        if role == Qt.ItemDataRole.BackgroundRole:
            if index.column() == self.COL_RECEIVED:
                token = "finance_received_missing_bg" if row.money_received is None else "finance_received_bg"
                return QBrush(color(token))
            if not row.values_complete or row.money_received is None:
                token = "finance_pending_even" if index.row() % 2 == 0 else "finance_pending_odd"
                return QBrush(color(token))
            if row.has_winner:
                token = "finance_winner_even" if index.row() % 2 == 0 else "finance_winner_odd"
                return QBrush(color(token))
            token = "finance_row_even" if index.row() % 2 == 0 else "finance_row_odd"
            return QBrush(color(token))
        if role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == self.COL_CONTACT:
                if row.whatsapp_phone:
                    return f"Contato configurado: {row.whatsapp_phone}"
                return "Contato n\u00e3o configurado"
            if index.column() == self.COL_BLOCK:
                return "Clique para abrir este bloco nos lan\u00e7amentos"
            if index.column() == self.COL_RECEIVED:
                if getattr(row, "money_fiado", False):
                    return "FIADO — clique para alterar o valor"
                return "Clique duas vezes para editar · 'f' = FIADO"
            if index.column() == self.COL_LIQUIDO:
                return "L\u00edquido da banca neste bloco (70%)"
            if index.column() == self.COL_SALDO:
                return "Saldo do bloco: dinheiro recebido - l\u00edquido (70%)"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == self.COL_RECEIVED:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() != self.COL_RECEIVED:
            return False
        self.last_exception = None
        row = self.rows[index.row()]
        payload = value if isinstance(value, dict) else {"text": value}
        text = payload.get("text", "")
        force_unlock = payload.get("force_unlock", False)
        try:
            self.controller.set_block_money(row.block_id, text, force_unlock=force_unlock)
            return True
        except Exception as exc:  # noqa: BLE001
            self.last_exception = exc
            return False

    def row_at(self, row: int):
        return self.rows[row]
