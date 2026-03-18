from __future__ import annotations

from PySide6.QtCore import QSize, Qt
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
            return QSize(option.rect.width(), 54 if compact else 70)
        if row.row_type == RowType.PAGE_HEADER:
            return QSize(option.rect.width(), 28 if compact else 34)
        if row.row_type == RowType.BET_ENTRY and row.is_trailing_blank:
            return QSize(option.rect.width(), 26 if compact else 30)
        return QSize(option.rect.width(), 24 if compact else 28)

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
        rect = option.rect.adjusted(8, 3, -12, -3)

        text = str(index.data() or "")
        if not text:
            return
        font = QFont(painter.font())
        pen_color = color("text")
        if row.line_ref is not None:
            if row.line_ref.value is not None:
                font.setPointSizeF(9.5 if getattr(self.view, "compact_mode", False) else 10.0)
                font.setBold(True)
            else:
                font.setPointSizeF(8.0 if getattr(self.view, "compact_mode", False) else 8.5)
                font.setItalic(True)
                pen_color = color("placeholder")
            if row.line_ref.is_error:
                pen_color = color("danger_fg")
            elif row.line_ref.winners:
                pen_color = color("success_fg")

        painter.setFont(font)
        text_metrics = painter.fontMetrics()
        pill_width = max(32, text_metrics.horizontalAdvance(text) + 8)
        pill_rect = rect.adjusted(max(0, rect.width() - pill_width), 0, 0, 0)

        if row.line_ref is not None and (row.line_ref.winners or row.line_ref.is_error or active):
            pill_fill = QColor(bet_entry_fill(row))
            if row.line_ref.winners:
                pill_fill.setAlpha(20)
            elif row.line_ref.is_error:
                pill_fill.setAlpha(18)
            else:
                pill_fill = QColor(SELECTION_FILL)
                pill_fill.setAlpha(14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(pill_fill)
            painter.drawRoundedRect(pill_rect, 7, 7)

        if active:
            border = QColor(color("focus"))
            border.setAlpha(68)
            painter.setPen(QPen(border, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(pill_rect.adjusted(0, 0, -1, -1), 7, 7)

        painter.setFont(font)
        painter.setPen(pen_color)
        painter.drawText(
            rect.adjusted(2, 0, -2, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            text,
        )
        painter.restore()
