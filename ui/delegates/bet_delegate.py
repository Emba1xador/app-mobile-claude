from __future__ import annotations

import unicodedata

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLineEdit, QStyledItemDelegate, QStyle

from core.entities import BetSpec
from core.enums import BetType, CommitMode, RowType
from ui.models.bets_table_model import BetsTableModel
from ui.theme import (
    BLOCK_PALETTES,
    ERROR_FILL,
    FLAG_COLORS,
    SELECTION_FILL,
    TYPE_COLORS,
    WINNER_FILL,
    color,
    tinted,
)


def block_palette(row) -> dict[str, QColor]:
    return BLOCK_PALETTES[bool(getattr(row, "block_is_even", False))]


def bet_entry_fill(row) -> QColor:
    line = row.line_ref
    if line is not None and line.winners:
        return WINNER_FILL
    if line is not None and line.is_error:
        return ERROR_FILL
    palette = block_palette(row)
    if line is None or line.is_empty:
        return palette["empty"]
    return palette["row_dark" if row.bet_row_is_even else "row_light"]


def is_current_row(option, index) -> bool:
    widget = option.widget
    if widget is None or not widget.currentIndex().isValid():
        return False
    return widget.currentIndex().row() == index.row()


def normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in folded if not unicodedata.combining(character))


class NavigationLineEdit(QLineEdit):
    commitRequested = Signal(str, object)
    actionRequested = Signal(str)

    def __init__(
        self,
        allow_comma_action: bool = False,
        allow_block_action: bool = False,
        shift_to_commit: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.allow_comma_action = allow_comma_action
        self.allow_block_action = allow_block_action
        self.shift_to_commit = shift_to_commit
        self.setTextMargins(0, 2, 0, 4)
        self.setMinimumHeight(32)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Up:
            self.actionRequested.emit("extend_up")
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Down:
            self.actionRequested.emit("extend_down")
            event.accept()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.commitRequested.emit("next", CommitMode.ENTER)
            event.accept()
            return
        if key == Qt.Key.Key_Up:
            self.commitRequested.emit("up", CommitMode.ENTER)
            event.accept()
            return
        if key == Qt.Key.Key_Down:
            self.commitRequested.emit("down", CommitMode.ENTER)
            event.accept()
            return
        if self.allow_block_action and modifiers == Qt.KeyboardModifier.NoModifier and key == Qt.Key.Key_B:
            self.actionRequested.emit("new_block")
            event.accept()
            return
        if self.shift_to_commit and key == Qt.Key.Key_Shift:
            self.commitRequested.emit("next", CommitMode.SHIFT_MC)
            event.accept()
            return
        if self.allow_comma_action and modifiers & Qt.KeyboardModifier.KeypadModifier and key == Qt.Key.Key_Comma:
            self.actionRequested.emit("new_page")
            event.accept()
            return
        if self.allow_comma_action and event.text() == ",":
            self.actionRequested.emit("new_page")
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.KeypadModifier and key == Qt.Key.Key_Minus:
            self.actionRequested.emit("flag_iv")
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.KeypadModifier and key == Qt.Key.Key_Plus:
            self.actionRequested.emit("flag_de")
            event.accept()
            return
        if modifiers & Qt.KeyboardModifier.KeypadModifier and key == Qt.Key.Key_Asterisk:
            self.actionRequested.emit("flag_dem")
            event.accept()
            return
        super().keyPressEvent(event)


# ═══════════════════════════════════════════════════════════════════
#  NEW DESIGN — BetDelegate v2
#  Clear hierarchy: Block (big card) > Page (section bar) > Bet (data row)
#  Bigger numbers, bigger badges, less wasted space
# ═══════════════════════════════════════════════════════════════════

# Layout constants
_MARGIN_LEFT = 8       # Left margin for ALL content
_MARGIN_RIGHT = 8      # Right margin
_BLOCK_INSET = 4       # Block card inset from edges
_PAGE_INSET = 12       # Page bar inset (slightly inside block)
_BET_INSET = 20        # Bet row left start (inside page context)
_BET_BADGE_GAP = 10    # Gap between badge and number
_BET_NUMBER_SIZE = 13.0  # Primary number font size (was 10.5!)
_BET_NUMBER_SIZE_COMPACT = 11.5
_BADGE_FONT_SIZE = 7.8    # Badge text (was 6.6!)
_BADGE_FONT_SIZE_SMALL = 7.0
_BADGE_HEIGHT = 17
_BADGE_HEIGHT_SMALL = 14
_BADGE_RADIUS = 5


class BetDelegate(QStyledItemDelegate):
    def __init__(self, view) -> None:
        super().__init__(view)
        self.view = view

    def createEditor(self, parent, option, index):
        editor = NavigationLineEdit(
            allow_comma_action=True,
            allow_block_action=True,
            shift_to_commit=True,
            parent=parent,
        )
        editor.setFrame(False)
        editor.commitRequested.connect(lambda direction, mode: self.view.commit_bet_editor(editor, direction, mode))
        editor.actionRequested.connect(lambda action: self.view.handle_editor_action(index, action, editor))
        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.model().data(index, Qt.ItemDataRole.EditRole) or "")
        editor.selectAll()

    def sizeHint(self, option, index):
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
        row = index.model().data(index, BetsTableModel.ROW_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        # ── Block card frame — continuous card for all rows in a block ──
        self._paint_block_card_frame(painter, option, index, row)

        if row.row_type == RowType.BLOCK_HEADER:
            self._paint_block_header(painter, option, row)
        elif row.row_type == RowType.PAGE_HEADER:
            self._paint_page_header(painter, option, row)
        else:
            self._paint_bet_line(painter, option, index, row)
        painter.restore()

    # ══════════════════════════════════════════════════════════════
    #  BLOCK CARD FRAME — continuous card enclosing all rows in a block
    # ══════════════════════════════════════════════════════════════

    def _paint_block_card_frame(self, painter: QPainter, option, index, row) -> None:
        is_first = row.row_type == RowType.BLOCK_HEADER
        model = index.model()
        next_idx = index.row() + 1
        is_last = True
        if next_idx < model.rowCount():
            next_row = model.data(model.index(next_idx, 0), BetsTableModel.ROW_ROLE)
            if next_row and next_row.block_id == row.block_id:
                is_last = False

        current = self.view.controller.state.ui_state.selected_block_id == row.block_id

        rect = QRectF(option.rect)
        # First row gets extra top margin to separate from previous card
        top_offset = 6.0 if is_first else 0.0
        bot_offset = 4.0 if is_last else 0.0
        card_rect = QRectF(
            rect.left() + 6,
            rect.top() + top_offset,
            rect.width() - 12,
            rect.height() - top_offset - bot_offset,
        )
        radius = 8.0

        # Card fill — slightly lighter than window bg to stand out
        if current:
            fill = QColor(55, 60, 72)  # slate highlight
        else:
            fill = QColor(45, 50, 62)  # slate card
        border_clr = QColor(74, 78, 90)  # visible slate border

        # Build path with rounded corners only at top/bottom of block
        path = QPainterPath()
        if is_first and is_last:
            path.addRoundedRect(card_rect, radius, radius)
        elif is_first:
            path.moveTo(card_rect.left(), card_rect.bottom())
            path.lineTo(card_rect.left(), card_rect.top() + radius)
            path.quadTo(card_rect.left(), card_rect.top(), card_rect.left() + radius, card_rect.top())
            path.lineTo(card_rect.right() - radius, card_rect.top())
            path.quadTo(card_rect.right(), card_rect.top(), card_rect.right(), card_rect.top() + radius)
            path.lineTo(card_rect.right(), card_rect.bottom())
            path.closeSubpath()
        elif is_last:
            path.moveTo(card_rect.left(), card_rect.top())
            path.lineTo(card_rect.left(), card_rect.bottom() - radius)
            path.quadTo(card_rect.left(), card_rect.bottom(), card_rect.left() + radius, card_rect.bottom())
            path.lineTo(card_rect.right() - radius, card_rect.bottom())
            path.quadTo(card_rect.right(), card_rect.bottom(), card_rect.right(), card_rect.bottom() - radius)
            path.lineTo(card_rect.right(), card_rect.top())
            path.closeSubpath()
        else:
            path.addRect(card_rect)

        # Draw card with shadow effect — slight offset darker rect behind
        if is_first:
            shadow = QPainterPath()
            shadow_rect = card_rect.adjusted(1, 1, 1, 0)
            shadow.addRoundedRect(shadow_rect, radius, radius)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 18))
            painter.drawPath(shadow)

        painter.setPen(QPen(border_clr, 1.0))
        painter.setBrush(fill)
        painter.drawPath(path)

        # For middle/last rows, ensure continuous side borders
        if not is_first:
            painter.setPen(QPen(border_clr, 1.0))
            painter.drawLine(int(card_rect.left()), int(card_rect.top()), int(card_rect.left()), int(card_rect.bottom()))
            painter.drawLine(int(card_rect.right()), int(card_rect.top()), int(card_rect.right()), int(card_rect.bottom()))

    # ══════════════════════════════════════════════════════════════
    #  BLOCK HEADER — Big prominent card
    # ══════════════════════════════════════════════════════════════

    def _paint_block_header(self, painter: QPainter, option, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        current = self.view.controller.state.ui_state.selected_block_id == row.block_id
        flashed = getattr(self.view, "_flash_block_id", None) == row.block_id
        expanded = row.block_id in self.view.model().expanded_block_ids

        rect = QRectF(option.rect)
        card = QRectF(
            rect.left() + _BLOCK_INSET + 4,
            rect.top() + (4 if not compact else 2),
            rect.width() - _BLOCK_INSET * 2 - 8,
            rect.height() - (6 if not compact else 4),
        )

        # ── Header zone — slightly lighter within the block card ──
        header_fill = QColor(255, 255, 255, 14) if current else QColor(255, 255, 255, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(header_fill)
        painter.drawRoundedRect(card, 6, 6)

        # ── Arrow ──
        arrow_x = card.left() + 12
        arrow_font = QFont(painter.font())
        arrow_font.setPointSizeF(11.0 if not compact else 9.5)
        arrow_font.setBold(True)
        painter.setFont(arrow_font)
        arrow_rect = QRectF(arrow_x, card.top(), 18, card.height())
        painter.setPen(color("title") if current else color("text_muted"))
        painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter,
                         "\u25be" if expanded else "\u25b8")

        # ── Block number (big, bold) ──
        title_left = arrow_x + 22
        title_font = QFont(painter.font())
        title_font.setPointSizeF(14.0 if not compact else 12.0)
        title_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(title_font)
        painter.setPen(color("title") if (current or flashed) else color("text"))

        # Split into two lines: title on top half, meta on bottom half
        top_half = QRectF(title_left, card.top(), card.right() - title_left - 10, card.height() * 0.55)
        bot_half = QRectF(title_left, card.top() + card.height() * 0.50, card.right() - title_left - 10, card.height() * 0.45)

        # State badge on same line as title
        state_text, state_color = self._block_state_text(row, current=current)
        state_right_margin = 0
        if state_text:
            state_font = QFont(painter.font())
            state_font.setPointSizeF(7.8 if not compact else 7.2)
            state_font.setBold(True)
            sfm = QFontMetrics(state_font)
            state_w = sfm.horizontalAdvance(state_text) + 22
            state_right_margin = state_w + 8

            state_rect = QRectF(card.right() - state_w - 12, card.top(), state_w, card.height() * 0.55)

            # dot
            dot_r = 4
            dot_rect = QRectF(state_rect.left(), state_rect.center().y() - dot_r / 2, dot_r, dot_r)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(state_color)
            painter.drawEllipse(dot_rect)

            painter.setFont(state_font)
            painter.setPen(state_color)
            painter.drawText(
                state_rect.adjusted(dot_r + 6, 0, 0, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                state_text,
            )

        # Draw block title
        painter.setFont(title_font)
        painter.setPen(color("title") if (current or flashed) else color("text"))
        title_available = top_half.width() - state_right_margin
        elided_title = QFontMetrics(title_font).elidedText(
            row.left_text, Qt.TextElideMode.ElideRight, int(title_available)
        )
        painter.drawText(
            QRectF(top_half.left(), top_half.top(), title_available, top_half.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided_title,
        )

        # ── Metrics line (bottom half) ──
        meta_font = QFont(painter.font())
        meta_font.setPointSizeF(8.2 if not compact else 7.4)
        meta_font.setWeight(QFont.Weight.Medium)
        painter.setFont(meta_font)
        painter.setPen(color("text_subtle"))
        metrics_text = self._block_metrics_text(row)
        painter.drawText(bot_half, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, metrics_text)

    # ══════════════════════════════════════════════════════════════
    #  PAGE HEADER — Clear section divider bar
    # ══════════════════════════════════════════════════════════════

    def _paint_page_header(self, painter: QPainter, option, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        current_page_id = self.view.controller.state.ui_state.selected_page_id
        current = current_page_id == row.page_id

        rect = QRectF(option.rect)

        # ── Separator line at top — divides pages within the card ──
        card_left = rect.left() + 4 + 12
        card_right = rect.right() - 4 - 12
        painter.setPen(QPen(QColor(255, 255, 255, 28), 1.0))
        painter.drawLine(int(card_left), int(rect.top() + 2), int(card_right), int(rect.top() + 2))

        # ── Section bar ──
        bar_rect = QRectF(
            rect.left() + _PAGE_INSET + 4,
            rect.top() + 4,
            rect.width() - _PAGE_INSET * 2 - 8,
            rect.height() - 6,
        )

        # Background — subtle shading within the card
        if current:
            bar_fill = QColor(255, 255, 255, 22)
        else:
            bar_fill = QColor(255, 255, 255, 10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_fill)
        painter.drawRoundedRect(bar_rect, 5, 5)

        # ── Page label ──
        text_left = bar_rect.left() + 12
        title_font = QFont(painter.font())
        title_font.setPointSizeF(10.0 if not compact else 9.0)
        title_font.setWeight(QFont.Weight.Bold)
        painter.setFont(title_font)

        page_label = f"Página {row.page_number}"
        title_fm = QFontMetrics(title_font)
        title_w = title_fm.horizontalAdvance(page_label)

        painter.setPen(color("title") if current else color("text"))
        title_rect = QRectF(text_left, bar_rect.top(), title_w + 4, bar_rect.height())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, page_label)

        # ── Meta info (bet count) ──
        meta = self._page_meta_text(row)
        if meta and meta != "Sem apostas":
            meta_font = QFont(painter.font())
            meta_font.setPointSizeF(8.0 if not compact else 7.4)
            meta_font.setWeight(QFont.Weight.Normal)
            painter.setFont(meta_font)
            painter.setPen(color("text_subtle"))
            meta_rect = QRectF(text_left + title_w + 10, bar_rect.top(), bar_rect.width() - title_w - 120, bar_rect.height())
            painter.drawText(meta_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, meta)

        # ── Total value on right ──
        total_text = "" if self._should_hide_page_total(row) else row.right_text
        if total_text:
            total_font = QFont(painter.font())
            total_font.setPointSizeF(9.0 if not compact else 8.2)
            total_font.setWeight(QFont.Weight.Bold)
            painter.setFont(total_font)
            painter.setPen(color("text") if current else color("text_muted"))
            total_rect = QRectF(bar_rect.right() - 120, bar_rect.top(), 108, bar_rect.height())
            painter.drawText(total_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, total_text)

    # ══════════════════════════════════════════════════════════════
    #  BET LINE — Big numbers, clear badges, clean layout
    # ══════════════════════════════════════════════════════════════

    def _paint_bet_line(self, painter: QPainter, option, index, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        line = row.line_ref
        if line is None:
            return

        # Content area — starts much closer to left edge than before
        content_rect = QRectF(option.rect.adjusted(_BET_INSET, 2, -_MARGIN_RIGHT, -2))
        active = bool(option.state & QStyle.StateFlag.State_Selected) or is_current_row(option, index)

        # ── Row background — ONLY for special states, minimal decoration ──
        if line.winners:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(60, 200, 100, 45))
            painter.drawRoundedRect(content_rect, 6, 6)
        elif line.is_error:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(224, 80, 80, 40))
            painter.drawRoundedRect(content_rect, 6, 6)
        elif active:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(212, 138, 28, 50))
            painter.drawRoundedRect(content_rect, 6, 6)

        # ── Empty line = action row ──
        if line.is_empty:
            self._paint_action_row(painter, content_rect, compact, active)
            return

        # ── Error line ──
        if line.is_error:
            self._paint_error_row(painter, content_rect, line.raw_text or "Entrada inválida", compact)
            return

        spec = line.spec
        if spec is None:
            return

        # ── Layout: [BADGE] [NUMBER ......... ] [FLAGS] [PRIZE] ──
        inner_left = content_rect.left() + 12
        inner_right = content_rect.right() - 8

        # Type badge
        badge_y = int(content_rect.center().y() - _BADGE_HEIGHT / 2)
        type_text, number_text, flag_texts = self.display_tokens(spec)
        type_fg, type_bg = TYPE_COLORS.get(spec.bet_type, (color("text_muted"), color("surface_bg")))
        badge_end = self._draw_badge(
            painter,
            int(inner_left),
            badge_y,
            type_text,
            QColor(type_fg),
            QColor(type_bg),
            small=False,
        )

        # Prize text (right-aligned, if winner)
        prize_width = 0
        if row.right_text:
            prize_font = QFont(painter.font())
            prize_font.setPointSizeF(8.6 if compact else 9.2)
            prize_font.setWeight(QFont.Weight.Bold)
            painter.setFont(prize_font)
            pfm = QFontMetrics(prize_font)
            prize_width = pfm.horizontalAdvance(row.right_text) + 16
            prize_rect = QRectF(inner_right - prize_width, content_rect.top(), prize_width, content_rect.height())
            painter.setPen(color("success_detail"))
            painter.drawText(prize_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, row.right_text)

        # ── NUMBER — the main event, BIG and bold ──
        number_font = QFont(painter.font())
        number_font.setPointSizeF(_BET_NUMBER_SIZE_COMPACT if compact else _BET_NUMBER_SIZE)
        number_font.setWeight(QFont.Weight.Bold)
        painter.setFont(number_font)
        painter.setPen(color("title") if (active or line.winners) else color("bet_text"))

        number_left = badge_end + _BET_BADGE_GAP
        number_right = inner_right - prize_width - 8
        number_rect = QRectF(number_left, content_rect.top(), max(0, number_right - number_left), content_rect.height())
        nfm = QFontMetrics(number_font)
        number_actual_w = nfm.horizontalAdvance(number_text)
        painter.drawText(number_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, number_text)

        # ── Flag badges (after number) ──
        flag_x = int(number_left + number_actual_w + 10)
        flag_badge_y = int(content_rect.center().y() - _BADGE_HEIGHT_SMALL / 2)
        for flag_text, flag in zip(flag_texts, spec.flags, strict=False):
            fg, bg = FLAG_COLORS.get(flag, (color("text_muted"), color("surface_bg")))
            if flag_x >= number_right - 28:
                break
            flag_x = self._draw_badge(
                painter,
                flag_x,
                flag_badge_y,
                flag_text,
                QColor(fg),
                QColor(bg),
                small=True,
            ) + 6

    # ══════════════════════════════════════════════════════════════
    #  ACTION ROW — "+ Nova aposta"
    # ══════════════════════════════════════════════════════════════

    def _paint_action_row(self, painter: QPainter, rect: QRectF, compact: bool, active: bool) -> None:
        # Simple text-only action — lightweight, no heavy box
        text_color = color("focus_strong") if active else color("text_subtle")
        font = QFont(painter.font())
        font.setPointSizeF(9.0 if not compact else 8.4)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(text_color)
        text_rect = QRectF(rect.left() + 14, rect.top(), rect.width() - 28, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "+ Nova aposta")

    # ══════════════════════════════════════════════════════════════
    #  ERROR ROW
    # ══════════════════════════════════════════════════════════════

    def _paint_error_row(self, painter: QPainter, rect: QRectF, text: str, compact: bool) -> None:
        inner_left = rect.left() + 12
        badge_y = int(rect.center().y() - _BADGE_HEIGHT / 2)
        badge_end = self._draw_badge(
            painter,
            int(inner_left),
            badge_y,
            "ERRO",
            color("danger_fg"),
            color("danger_bg"),
            small=False,
        )
        error_rect = QRectF(badge_end + 12, rect.top(), rect.right() - badge_end - 20, rect.height())
        font = QFont(painter.font())
        font.setPointSizeF(11.0 if not compact else 10.0)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(color("danger_fg"))
        elided = QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, int(error_rect.width()))
        painter.drawText(error_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, elided)

    # ══════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════

    def _block_metrics_text(self, row) -> str:
        page_label = "1 página" if row.block_page_count == 1 else f"{row.block_page_count} páginas"
        bet_label = "1 aposta" if row.block_bet_count == 1 else f"{row.block_bet_count} apostas"
        return f"{page_label}  •  {bet_label}"

    def _block_state_text(self, row, *, current: bool) -> tuple[str, QColor]:
        if current:
            return "em edição", color("focus_strong")
        if row.block_prize_count > 0:
            label = "1 prêmio" if row.block_prize_count == 1 else f"{row.block_prize_count} prêmios"
            return label, color("success_detail")
        if row.block_pendency_count > 0:
            label = "1 pendência" if row.block_pendency_count == 1 else f"{row.block_pendency_count} pendências"
            return label, color("warning_detail")
        return "", color("text_muted")

    def _page_meta_text(self, row) -> str:
        page = row.page_ref
        if page is None:
            return "Sem apostas"
        valid_lines = [line for line in page.lines if line.is_valid_bet]
        if not valid_lines:
            return "Sem apostas"
        winner_count = sum(1 for line in page.lines if line.winners)
        parts = ["1 aposta" if len(valid_lines) == 1 else f"{len(valid_lines)} apostas"]
        if winner_count > 0:
            parts.append("1 prêmio" if winner_count == 1 else f"{winner_count} prêmios")
        return " • ".join(parts)

    def _should_hide_page_total(self, row) -> bool:
        return row.valid_bet_count == 0 and row.right_text.strip() == "R$ 0,00"

    def _page_status(self, row) -> tuple[str, QColor, QColor]:
        page = row.page_ref
        if page is None:
            return "", color("text_muted"), tinted("surface_bg", 200)
        valid_lines = [line for line in page.lines if line.is_valid_bet]
        winner_count = sum(1 for line in page.lines if line.winners)
        if winner_count:
            text = "1 prêmio" if winner_count == 1 else f"{winner_count} prêmios"
            return text, color("success_fg"), color("success_bg")
        if any(line.is_error for line in page.lines):
            return "Revisar", color("danger_fg"), color("danger_bg")
        if not valid_lines:
            return "Vazia", color("text_muted"), tinted("surface_alt", 210)
        if any(line.value is None for line in valid_lines):
            return "Pendente", color("warning_fg"), color("warning_bg")
        return "Concluída", color("success_fg"), color("success_bg")

    def _summary_color(self, row) -> QColor:
        summary = normalized_text(row.right_text)
        if "edicao" in summary:
            return color("focus_strong")
        if "premio" in summary and "sem premio" not in summary:
            return color("success_detail")
        if "pendencia" in summary or "pendente" in summary:
            return color("warning_detail")
        return color("text_muted")

    def display_tokens(self, spec: BetSpec) -> tuple[str, str, list[str]]:
        number_text = " / ".join(spec.numbers) if spec.bet_type == BetType.FECHAMENTO else " ".join(spec.numbers)
        return spec.bet_type.value, number_text, [flag.value for flag in spec.flags]

    def _draw_badge(
        self,
        painter: QPainter,
        x: int,
        y: int,
        text: str,
        fg: QColor,
        bg: QColor,
        *,
        small: bool = False,
    ) -> int:
        font = QFont(painter.font())
        font.setPointSizeF(_BADGE_FONT_SIZE_SMALL if small else _BADGE_FONT_SIZE)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        padding_x = 8 if not small else 6
        width = metrics.horizontalAdvance(text) + (padding_x * 2)
        height = _BADGE_HEIGHT_SMALL if small else _BADGE_HEIGHT
        badge_rect = QRectF(x, y, width, height)

        # Solid fill — no border, clean pill
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(badge_rect, _BADGE_RADIUS, _BADGE_RADIUS)

        # Text
        painter.setPen(fg)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)
        return int(badge_rect.right())
