from __future__ import annotations

import unicodedata

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont

from app_state.projections import build_bets_projection
from core.enums import CommitMode, RowType
from services.formatting import format_money
from ui.theme import BLOCK_PALETTES, ERROR_FILL, WINNER_FILL, color


def _normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in folded if not unicodedata.combining(character))


class BetsTableModel(QAbstractTableModel):
    ROW_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self.filter_mode = "all"
        self.expanded_block_ids: set[str] = {block.block_id for block in self.controller.state.blocks}
        self.rows = self._build_rows()
        self.last_exception: Exception | None = None
        self.controller.subscribe(self.refresh)

    def _build_rows(self):
        selected_block_id = self.controller.state.ui_state.selected_block_id
        selected_page_id = self.controller.state.ui_state.selected_page_id
        block_ids = {block.block_id for block in self.controller.state.blocks}
        self.expanded_block_ids &= block_ids
        if not self.expanded_block_ids:
            self.expanded_block_ids = set(block_ids)
        return build_bets_projection(
            self.controller.state.blocks,
            filter_mode=self.filter_mode,
            selected_block_id=selected_block_id,
            selected_page_id=selected_page_id,
            expanded_block_ids=self.expanded_block_ids,
        )

    def refresh(self) -> None:
        self.beginResetModel()
        self.rows = self._build_rows()
        self.endResetModel()

    def set_filter_mode(self, filter_mode: str) -> None:
        if self.filter_mode == filter_mode:
            return
        self.filter_mode = filter_mode
        self.refresh()

    def toggle_block_expansion(self, block_id: str) -> None:
        if block_id in self.expanded_block_ids:
            self.expanded_block_ids.remove(block_id)
        else:
            self.expanded_block_ids.add(block_id)
        self.refresh()

    def ensure_block_expanded(self, block_id: str) -> None:
        if block_id in self.expanded_block_ids:
            return
        self.expanded_block_ids.add(block_id)
        self.refresh()

    def refresh_external_values(self, line_ids: set[str], page_ids: set[str], block_ids: set[str] | None = None) -> None:
        block_ids = set(block_ids or ())
        for row_index, row in enumerate(self.rows):
            if row.line_id in line_ids:
                left_index = self.index(row_index, 0)
                right_index = self.index(row_index, 1)
                self.dataChanged.emit(left_index, right_index)
            elif row.row_type == RowType.PAGE_HEADER and row.page_id in page_ids:
                index = self.index(row_index, 0)
                self.dataChanged.emit(index, index)
            elif row.row_type == RowType.BLOCK_HEADER and row.block_id in block_ids:
                index = self.index(row_index, 0)
                self.dataChanged.emit(index, index)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def headerData(self, section: int, orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        return ["Aposta", "Valor"][section]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        if role == self.ROW_ROLE:
            return row
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return row.left_text
            if row.row_type == RowType.BLOCK_HEADER:
                return row.right_text
            if row.row_type == RowType.PAGE_HEADER:
                return row.right_text
            if row.row_type == RowType.BET_ENTRY and row.line_ref is not None:
                if row.is_trailing_blank:
                    return ""
                if row.line_ref.value is None:
                    return ""
                return format_money(row.line_ref.value)
            return row.right_text
        if role == Qt.ItemDataRole.EditRole and row.row_type == RowType.BET_ENTRY and row.line_ref is not None:
            if index.column() == 0:
                return "" if row.is_trailing_blank else row.line_ref.raw_text
            if row.line_ref.value is None:
                return ""
            return format_money(row.line_ref.value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter | (
                Qt.AlignmentFlag.AlignRight if index.column() == 1 else Qt.AlignmentFlag.AlignLeft
            )
        if role == Qt.ItemDataRole.ForegroundRole:
            if row.row_type == RowType.BLOCK_HEADER and index.column() == 1:
                return QBrush(self._block_summary_color(row))
            if row.row_type == RowType.PAGE_HEADER and index.column() == 1:
                return QBrush(color("text_subtle"))
            if row.row_type == RowType.PAGE_HEADER and index.column() == 0:
                return QBrush(color("title"))
            if row.row_type == RowType.BET_ENTRY and index.column() == 1 and row.line_ref is not None:
                if row.line_ref.is_error:
                    return QBrush(color("danger_fg"))
                if row.line_ref.winners:
                    return QBrush(color("success_fg"))
                if row.line_ref.value is None:
                    return QBrush(color("placeholder"))
            return QBrush(color("text"))
        if role == Qt.ItemDataRole.BackgroundRole and index.column() == 1:
            if row.row_type == RowType.BET_ENTRY and row.line_ref is not None:
                if row.line_ref.winners:
                    return QBrush(WINNER_FILL)
                if row.line_ref.is_error:
                    return QBrush(ERROR_FILL)
                if row.line_ref.is_empty:
                    return QBrush(self._row_palette(row)["empty"])
                return QBrush(self._row_palette(row)["row_dark" if row.bet_row_is_even else "row_light"])
            return None
        if role == Qt.ItemDataRole.FontRole:
            font = QFont()
            if row.row_type == RowType.BLOCK_HEADER:
                if index.column() == 0:
                    font.setBold(True)
                    font.setPointSizeF(12.1)
                else:
                    font.setPointSizeF(8.2)
                return font
            if row.row_type == RowType.PAGE_HEADER:
                if index.column() == 0:
                    font.setPointSizeF(10.0)
                    font.setBold(True)
                else:
                    font.setPointSizeF(8.2)
                    font.setBold(False)
                return font
            if row.row_type == RowType.BET_ENTRY and index.column() == 0:
                if row.is_trailing_blank:
                    font.setPointSizeF(9.2)
                    font.setBold(True)
                    return font
                font.setPointSizeF(10.1)
                return font
            if row.row_type == RowType.BET_ENTRY and row.line_ref is not None and row.line_ref.value is not None and index.column() == 1:
                font.setPointSizeF(9.9)
                font.setBold(True)
                return font
        if role == Qt.ItemDataRole.ToolTipRole and row.row_type == RowType.BET_ENTRY and row.line_ref is not None:
            if row.is_trailing_blank:
                return "Criar uma nova aposta nesta página."
            if row.line_ref.is_error and row.line_ref.spec is not None:
                return row.line_ref.spec.error_message or "Entrada inválida"
            if row.line_ref.winners:
                return "\n".join(hit.detail for hit in row.line_ref.winners)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        row = self.rows[index.row()]
        base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if row.row_type == RowType.BET_ENTRY:
            if index.column() == 1 and row.is_trailing_blank:
                return base_flags
            if index.column() == 1 and row.line_ref is not None and not row.line_ref.is_valid_bet:
                return base_flags
            return base_flags | Qt.ItemFlag.ItemIsEditable
        return base_flags

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        row = self.rows[index.row()]
        if row.row_type != RowType.BET_ENTRY or row.line_ref is None:
            return False
        self.last_exception = None
        payload = value if isinstance(value, dict) else {"text": value}
        text = payload.get("text", "")
        commit_mode = payload.get("commit_mode", CommitMode.ENTER)
        force_unlock = payload.get("force_unlock", False)
        try:
            if index.column() == 0:
                self.controller.upsert_bet_text(
                    row.line_ref.line_id,
                    text,
                    commit_mode=commit_mode,
                    force_unlock=force_unlock,
                )
            else:
                self.controller.set_line_value(row.line_ref.line_id, text, force_unlock=force_unlock)
            return True
        except Exception as exc:  # noqa: BLE001
            self.last_exception = exc
            return False

    def row_at(self, row: int):
        return self.rows[row]

    def line_id_for_row(self, row: int) -> str | None:
        return self.rows[row].line_id

    def page_id_for_row(self, row: int) -> str:
        return self.rows[row].page_id

    def block_id_for_row(self, row: int) -> str:
        return self.rows[row].block_id

    def first_editable_row_for_page(self, page_id: str) -> int | None:
        for index, row in enumerate(self.rows):
            if row.page_id == page_id and row.row_type == RowType.BET_ENTRY and not row.is_trailing_blank:
                return index
        for index, row in enumerate(self.rows):
            if row.page_id == page_id and row.row_type == RowType.BET_ENTRY:
                return index
        return None

    def action_row_for_page(self, page_id: str) -> int | None:
        for index, row in enumerate(self.rows):
            if row.page_id == page_id and row.row_type == RowType.BET_ENTRY and row.is_trailing_blank:
                return index
        return None

    def page_header_row(self, page_id: str) -> int | None:
        for index, row in enumerate(self.rows):
            if row.page_id == page_id and row.row_type == RowType.PAGE_HEADER:
                return index
        return None

    def block_header_row(self, block_id: str) -> int | None:
        for index, row in enumerate(self.rows):
            if row.block_id == block_id and row.row_type == RowType.BLOCK_HEADER:
                return index
        return None

    def first_header_row_for_block(self, block_id: str) -> int | None:
        return self.block_header_row(block_id)

    def first_editable_row_for_block(self, block_id: str, column: int = 0) -> int | None:
        for index, row in enumerate(self.rows):
            if row.block_id != block_id or row.row_type != RowType.BET_ENTRY:
                continue
            if column == 1 and row.is_trailing_blank:
                continue
            return index
        return None

    def first_pending_editable_row_for_block(self, block_id: str, column: int = 0) -> int | None:
        for index, row in enumerate(self.rows):
            if row.block_id != block_id or row.row_type != RowType.BET_ENTRY or row.line_ref is None:
                continue
            if row.is_trailing_blank:
                continue
            if row.line_ref.is_valid_bet and row.line_ref.value is None:
                return index
            if row.line_ref.is_error:
                return index
        return self.first_editable_row_for_block(block_id, column=column)

    def _row_palette(self, row) -> dict[str, QColor]:
        return BLOCK_PALETTES[bool(getattr(row, "block_is_even", False))]

    def _block_summary_color(self, row) -> QColor:
        summary = _normalized_text(row.right_text)
        if "edicao" in summary:
            return color("focus_strong")
        if "premio" in summary and "sem premio" not in summary:
            return color("success_detail")
        if "pendencia" in summary or "pendente" in summary:
            return color("warning_detail")
        return color("text_muted")
