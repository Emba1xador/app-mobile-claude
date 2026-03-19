from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from core.enums import RowType
from ui.delegates.bet_delegate import NavigationLineEdit, SELECTION_FILL, bet_entry_fill, is_current_row
from ui.models.bets_table_model import BetsTableModel
from ui.theme import color


class ValueDelegate(QStyledItemDelegate):
    def __init__(self, view, finance: bool = False) -> None:
        super().__init__(view)
        self.view = view
        self.finance = finance

    def createEditor(self, parent, option, index):
        editor = NavigationLineEdit(allow_comma_action=False, shift_to_commit=False, parent=parent)
        editor.setFrame(False)
        if self.finance:
            editor.commitRequested.connect(lambda direction, mode: self.view.commit_finance_editor(editor))
        else:
            editor.commitRequested.connect(lambda direction, mode: self.view.commit_value_editor(editor, direction))
        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.model().data(index, Qt.ItemDataRole.EditRole) or "")
        editor.selectAll()

    def sizeHint(self, option, index):
        if self.finance:
            return super().sizeHint(option, index)
        row = index.model().data(index, BetsTableModel.ROW_ROLE)
        compact = bool(getattr(self.view, "compact_mode", False))
        if row.row_type == RowType.BLOCK_HEADER:
            return QSize(option.rect.width(), 58 if compact else 74)
        if row.row_type == RowType.PAGE_HEADER:
            return QSize(option.rect.width(), 32 if compact else 40)
        if row.row_type == RowType.BET_ENTRY and row.is_trailing_blank:
            return QSize(option.rect.width(), 30 if compact else 36)
        return QSize(option.rect.width(), 32 if compact else 38)

    def paint(self, painter: QPainter, option, index) -> None:
        if self.finance:
            super().paint(painter, option, index)
            return

        row = index.model().data(index, BetsTableModel.ROW_ROLE)
        if row.row_type != RowType.BET_ENTRY:
            return
        if row.is_trailing_blank:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        active = bool(option.state & QStyle.StateFlag.State_Selected) or is_current_row(option, index)
        rect = QRectF(option.rect.adjusted(4, 4, -8, -4))

        text = str(index.data() or "")
        if not text:
            painter.restore()
            return

        font = QFont(painter.font())
        pen_color = color("text")

        if row.line_ref is not None:
            if row.line_ref.value is not None:
                font.setPointSizeF(10.5 if getattr(self.view, "compact_mode", False) else 11.0)
                font.setWeight(QFont.Weight.Bold)
            else:
                font.setPointSizeF(8.5 if getattr(self.view, "compact_mode", False) else 9.0)
                font.setItalic(True)
                pen_color = color("placeholder")
            if row.line_ref.is_error:
                pen_color = color("danger_fg")
            elif row.line_ref.winners:
                pen_color = color("success_fg")

        painter.setFont(font)

        # No heavy decorations — just clean text

        painter.setFont(font)
        painter.setPen(pen_color)
        painter.drawText(
            rect.adjusted(4, 0, -4, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            text,
        )
        painter.restore()
