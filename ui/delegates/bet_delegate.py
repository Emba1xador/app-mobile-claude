from __future__ import annotations

import unicodedata

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
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
            return QSize(option.rect.width(), 54 if compact else 70)
        if row.row_type == RowType.PAGE_HEADER:
            return QSize(option.rect.width(), 28 if compact else 34)
        if row.row_type == RowType.BET_ENTRY and row.is_trailing_blank:
            return QSize(option.rect.width(), 26 if compact else 30)
        return QSize(option.rect.width(), 24 if compact else 28)

    def paint(self, painter: QPainter, option, index) -> None:
        row = index.model().data(index, BetsTableModel.ROW_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        if row.row_type == RowType.BLOCK_HEADER:
            self._paint_block_header(painter, option, row)
        elif row.row_type == RowType.PAGE_HEADER:
            self._paint_page_header(painter, option, row)
        else:
            self._paint_bet_line(painter, option, index, row)
        painter.restore()

    # ── Block header: prominent card with OPAQUE fills ─────────────

    def _paint_block_header(self, painter: QPainter, option, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        current = self.view.controller.state.ui_state.selected_block_id == row.block_id
        flashed = getattr(self.view, "_flash_block_id", None) == row.block_id
        expanded = row.block_id in self.view.model().expanded_block_ids

        card = QRectF(option.rect.adjusted(4, 6 if compact else 8, -6, -2 if compact else -4))

        # OPAQUE card fill — genuinely different from bg (#131C25)
        if current:
            fill_color = QColor(30, 52, 72)    # #1E3448 — clearly lighter
        elif flashed:
            fill_color = QColor(26, 45, 62)    # #1A2D3E
        else:
            fill_color = QColor(22, 38, 52)    # #162634 — still visibly different
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(card, 10, 10)

        # VISIBLE border — opaque, not alpha-blended
        if current:
            border_color = QColor(58, 100, 135)   # bright teal border
        elif flashed:
            border_color = QColor(48, 82, 110)
        else:
            border_color = QColor(38, 60, 78)     # muted but still visible
        painter.setPen(QPen(border_color, 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(card.adjusted(0.6, 0.6, -0.6, -0.6), 10, 10)

        # SOLID accent bar — full saturated color, no alpha reduction
        if current or flashed:
            bar_color = color("focus_strong")      # #73C4D5 — bright cyan
        else:
            bar_color = color("focus")             # #4B96AE — still clearly colored
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        bar_pad = 7 if compact else 9
        painter.drawRoundedRect(
            QRectF(card.left() + 6, card.top() + bar_pad, 4.0, card.height() - bar_pad * 2),
            2, 2,
        )

        # Layout: top half = title row, bottom half = metrics row
        content_left = card.left() + 18
        mid_y = card.top() + card.height() / 2

        # Arrow
        arrow_rect = QRectF(content_left, card.top(), 16, mid_y - card.top())
        arrow_font = QFont(painter.font())
        arrow_font.setPointSizeF(9.0 if compact else 10.0)
        arrow_font.setBold(True)
        painter.setFont(arrow_font)
        painter.setPen(color("title") if (current or flashed) else color("text_muted"))
        painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "\u25be" if expanded else "\u25b8")

        # State badge (top-right)
        state_text, state_color = self._block_state_text(row, current=current)
        state_width = 0
        if state_text:
            state_font = QFont(painter.font())
            state_font.setPointSizeF(7.0 if compact else 7.5)
            state_font.setBold(True)
            painter.setFont(state_font)
            state_width = QFontMetrics(state_font).horizontalAdvance(state_text) + 14
            state_rect = QRectF(card.right() - state_width - 10, card.top(), state_width, mid_y - card.top())
            dot_rect = QRectF(state_rect.left(), state_rect.center().y() - 2.5, 5, 5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(state_color)
            painter.drawEllipse(dot_rect)
            painter.setPen(state_color)
            painter.drawText(
                state_rect.adjusted(10, 0, 0, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                state_text,
            )

        # Title
        title_left = arrow_rect.right() + 6
        title_right = card.right() - (state_width + 22 if state_text else 14)
        title_rect = QRectF(title_left, card.top(), max(0.0, title_right - title_left), mid_y - card.top())
        title_font = QFont(painter.font())
        title_font.setPointSizeF(10.5 if compact else 12.0)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(color("title") if (current or flashed) else color("text"))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, row.left_text)

        # Metrics
        metrics_font = QFont(painter.font())
        metrics_font.setPointSizeF(7.0 if compact else 7.6)
        painter.setFont(metrics_font)
        painter.setPen(color("text_subtle"))
        metrics_rect = QRectF(title_left, mid_y, max(0.0, title_right - title_left), card.bottom() - mid_y)
        metrics_text = QFontMetrics(metrics_font).elidedText(
            self._block_metrics_text(row),
            Qt.TextElideMode.ElideRight,
            int(metrics_rect.width()),
        )
        painter.drawText(metrics_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, metrics_text)

    # ── Page header: visible left bar + label ──────────────────────

    def _paint_page_header(self, painter: QPainter, option, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        current_page_id = self.view.controller.state.ui_state.selected_page_id
        current = current_page_id == row.page_id

        rect = QRectF(option.rect)
        left_x = 94.0
        right_x = rect.right() - 12.0

        # Current page: tinted background
        if current:
            hl = QColor(40, 70, 95, 50)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(hl)
            painter.drawRoundedRect(
                QRectF(left_x, rect.top() + 2, right_x - left_x, rect.height() - 4), 7, 7,
            )

        # Top separator line — visible
        sep = QColor(45, 65, 82)
        painter.setPen(QPen(sep, 1.0))
        painter.drawLine(int(left_x + 4), int(rect.top() + 1), int(right_x), int(rect.top() + 1))

        # Left accent bar — solid, visible
        if current:
            bar_color = color("focus")             # #4B96AE — bright
        else:
            bar_color = QColor(55, 80, 100)        # muted teal — still clearly visible
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bar_color)
        bar_h = rect.height() - 12
        painter.drawRoundedRect(
            QRectF(left_x + 4, rect.center().y() - bar_h / 2, 3.0, bar_h), 1.5, 1.5,
        )

        # Page title
        text_left = left_x + 14
        title_font = QFont(painter.font())
        title_font.setPointSizeF(8.6 if compact else 9.2)
        title_font.setBold(True)
        painter.setFont(title_font)
        page_label = f"P\u00e1gina {row.page_number}"
        title_width = QFontMetrics(title_font).horizontalAdvance(page_label)

        # Total on right
        total_text = "" if self._should_hide_page_total(row) else row.right_text
        total_width = 0
        if total_text:
            total_font = QFont(painter.font())
            total_font.setPointSizeF(7.6 if compact else 8.0)
            total_font.setBold(True)
            painter.setFont(total_font)
            total_width = QFontMetrics(total_font).horizontalAdvance(total_text)
            total_rect = QRectF(right_x - total_width, rect.top(), total_width, rect.height())
            painter.setPen(color("text_subtle"))
            painter.drawText(total_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, total_text)

        # Draw title
        available = max(0.0, right_x - text_left - total_width - 16)
        title_rect = QRectF(text_left, rect.top(), min(title_width, available), rect.height())
        painter.setFont(title_font)
        painter.setPen(color("title") if current else color("text_muted"))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, page_label)

        # Meta inline
        meta = self._page_meta_text(row)
        if meta and meta != "Sem apostas" and title_width + 60 < available:
            meta_font = QFont(painter.font())
            meta_font.setPointSizeF(7.2 if compact else 7.8)
            meta_font.setBold(False)
            painter.setFont(meta_font)
            painter.setPen(color("text_subtle"))
            meta_left = text_left + title_width + 8
            meta_rect = QRectF(meta_left, rect.top(), max(0.0, available - title_width - 12), rect.height())
            painter.drawText(
                meta_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"\u00b7 {meta}",
            )

    # ── Bet line: clean data row ───────────────────────────────────

    def _paint_bet_line(self, painter: QPainter, option, index, row) -> None:
        compact = bool(getattr(self.view, "compact_mode", False))
        line = row.line_ref
        if line is None:
            return

        content_rect = QRectF(option.rect.adjusted(106, 1, -12, -1))
        active = bool(option.state & QStyle.StateFlag.State_Selected) or is_current_row(option, index)

        # Row fill for special states
        if line.winners or line.is_error or active:
            row_fill = bet_entry_fill(row)
            if line.winners:
                row_fill.setAlpha(14)
            elif line.is_error:
                row_fill.setAlpha(12)
            else:
                row_fill = QColor(SELECTION_FILL)
                row_fill.setAlpha(12)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(row_fill)
            painter.drawRoundedRect(content_rect, 7, 7)

        if line.winners:
            accent = QColor(color("success_detail"))
            accent.setAlpha(184)
            painter.setBrush(accent)
            painter.drawRoundedRect(QRectF(content_rect.left(), content_rect.top() + 4, 2.0, content_rect.height() - 8), 1.1, 1.1)
            border = QColor(color("success_detail"))
            border.setAlpha(28)
            painter.setPen(QPen(border, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(content_rect.adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)
            painter.setPen(Qt.PenStyle.NoPen)
        elif line.is_error:
            accent = QColor(color("danger_detail"))
            accent.setAlpha(164)
            painter.setBrush(accent)
            painter.drawRoundedRect(QRectF(content_rect.left(), content_rect.top() + 4, 2.0, content_rect.height() - 8), 1.1, 1.1)

        if active:
            active_border = QColor(color("focus"))
            active_border.setAlpha(54)
            painter.setPen(QPen(active_border, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(content_rect.adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color("focus_strong"))
            painter.drawRoundedRect(QRectF(content_rect.left(), content_rect.top() + 4, 2.0, content_rect.height() - 8), 1.1, 1.1)

        if line.is_empty:
            self._paint_action_row(painter, content_rect, compact, active)
            return

        if line.is_error:
            self._paint_error_row(painter, content_rect, line.raw_text or "Entrada inv\u00e1lida", compact)
            return

        spec = line.spec
        if spec is None:
            return

        badge_y = int(content_rect.top() + (4 if compact else 5))
        type_text, number_text, flag_texts = self.display_tokens(spec)
        type_fg, type_bg = TYPE_COLORS.get(spec.bet_type, (color("text_muted"), color("surface_bg")))
        type_end = self._draw_badge(
            painter,
            int(content_rect.left() + 12),
            badge_y,
            type_text,
            QColor(type_fg),
            QColor(type_bg),
            small=True,
        )

        prize_rect = QRectF(content_rect.right() - 128, content_rect.top(), 122, content_rect.height())
        if row.right_text:
            prize_font = QFont(painter.font())
            prize_font.setPointSizeF(7.4 if compact else 7.9)
            prize_font.setBold(True)
            painter.setFont(prize_font)
            painter.setPen(color("success_detail"))
            prize_text = QFontMetrics(prize_font).elidedText(
                row.right_text,
                Qt.TextElideMode.ElideLeft,
                int(prize_rect.width()),
            )
            painter.drawText(prize_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, prize_text)

        primary_font = QFont(painter.font())
        primary_font.setPointSizeF(9.8 if compact else 10.5)
        primary_font.setBold(True)
        painter.setFont(primary_font)
        painter.setPen(color("bet_text"))

        number_left = max(int(content_rect.left() + 68), type_end + 12)
        number_right = int(prize_rect.left() - 12) if row.right_text else int(content_rect.right() - 12)
        number_rect = QRectF(number_left, content_rect.top(), max(0, number_right - number_left), content_rect.height())
        number_width = min(QFontMetrics(primary_font).horizontalAdvance(number_text), int(number_rect.width()))
        painter.drawText(number_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, number_text)

        flag_x = int(number_rect.left()) + number_width + 10
        for flag_text, flag in zip(flag_texts, spec.flags, strict=False):
            fg, bg = FLAG_COLORS.get(flag, (color("text_muted"), color("surface_bg")))
            if flag_x >= number_right - 28:
                break
            flag_x = self._draw_badge(
                painter,
                flag_x,
                badge_y + (2 if compact else 3),
                flag_text,
                QColor(fg),
                QColor(bg),
                small=True,
            ) + 5

    # ── Action row ─────────────────────────────────────────────────

    def _paint_action_row(self, painter: QPainter, rect: QRectF, compact: bool, active: bool) -> None:
        button_width = min(rect.width() - 12, 150 if compact else 168)
        action_rect = QRectF(rect.left() + 4, rect.top() + 2, button_width, rect.height() - 4)
        fill = QColor(color("surface_alt"))
        fill.setAlpha(20 if active else 10)
        border = QColor(color("focus") if active else color("divider"))
        border.setAlpha(56 if active else 24)
        painter.setPen(QPen(border, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(action_rect, 8, 8)

        plus_color = QColor(color("focus_strong") if active else color("text_muted"))
        plus_color.setAlpha(196 if active else 142)
        plus_rect = QRectF(action_rect.left() + 10, action_rect.center().y() - 6, 12, 12)
        bubble_fill = QColor(color("surface_alt"))
        bubble_fill.setAlpha(34 if active else 18)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bubble_fill)
        painter.drawEllipse(plus_rect)
        painter.setPen(QPen(plus_color, 1.3))
        painter.drawLine(
            int(plus_rect.center().x()),
            int(plus_rect.top() + 4),
            int(plus_rect.center().x()),
            int(plus_rect.bottom() - 4),
        )
        painter.drawLine(
            int(plus_rect.left() + 4),
            int(plus_rect.center().y()),
            int(plus_rect.right() - 4),
            int(plus_rect.center().y()),
        )

        font = QFont(painter.font())
        font.setPointSizeF(8.3 if compact else 8.8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color("focus_strong") if active else color("text_subtle"))
        painter.drawText(
            action_rect.adjusted(30, 0, -12, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "+ Nova aposta",
        )

    # ── Error row ──────────────────────────────────────────────────

    def _paint_error_row(self, painter: QPainter, rect: QRectF, text: str, compact: bool) -> None:
        badge_end = self._draw_badge(
            painter,
            int(rect.left() + 10),
            int(rect.top() + (4 if compact else 5)),
            "ERRO",
            color("danger_fg"),
            color("danger_bg"),
            small=compact,
        )
        error_rect = QRectF(badge_end + 10, rect.top(), rect.width() - (badge_end - rect.left()) - 20, rect.height())
        font = QFont(painter.font())
        font.setPointSizeF(9.4 if compact else 10.0)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color("danger_fg"))
        painter.drawText(error_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

    # ── Helpers ────────────────────────────────────────────────────

    def _block_metrics_text(self, row) -> str:
        page_label = "1 p\u00e1gina" if row.block_page_count == 1 else f"{row.block_page_count} p\u00e1ginas"
        bet_label = "1 aposta" if row.block_bet_count == 1 else f"{row.block_bet_count} apostas"
        return f"{page_label} \u2022 {bet_label}"

    def _block_state_text(self, row, *, current: bool) -> tuple[str, QColor]:
        if current:
            return "em edi\u00e7\u00e3o", color("focus_strong")
        if row.block_prize_count > 0:
            label = "1 pr\u00eamio" if row.block_prize_count == 1 else f"{row.block_prize_count} pr\u00eamios"
            return label, color("success_detail")
        if row.block_pendency_count > 0:
            label = "1 pend\u00eancia" if row.block_pendency_count == 1 else f"{row.block_pendency_count} pend\u00eancias"
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
            parts.append("1 pr\u00eamio" if winner_count == 1 else f"{winner_count} pr\u00eamios")
        return " \u2022 ".join(parts)

    def _should_hide_page_total(self, row) -> bool:
        return row.valid_bet_count == 0 and row.right_text.strip() == "R$ 0,00"

    def _page_status(self, row) -> tuple[str, QColor, QColor]:
        page = row.page_ref
        if page is None:
            return "", color("text_muted"), tinted("surface_bg", 200)
        valid_lines = [line for line in page.lines if line.is_valid_bet]
        winner_count = sum(1 for line in page.lines if line.winners)
        if winner_count:
            text = "1 pr\u00eamio" if winner_count == 1 else f"{winner_count} pr\u00eamios"
            return text, color("success_fg"), color("success_bg")
        if any(line.is_error for line in page.lines):
            return "Revisar", color("danger_fg"), color("danger_bg")
        if not valid_lines:
            return "Vazia", color("text_muted"), tinted("surface_alt", 210)
        if any(line.value is None for line in valid_lines):
            return "Pendente", color("warning_fg"), color("warning_bg")
        return "Conclu\u00edda", color("success_fg"), color("success_bg")

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

    def _badge_width(self, text: str, *, small: bool = False) -> int:
        font = QFont()
        font.setPointSizeF(6.6 if small else 7.5)
        font.setBold(True)
        metrics = QFontMetrics(font)
        padding_x = 4 if small else 6
        return metrics.horizontalAdvance(text) + (padding_x * 2)

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
        font.setPointSizeF(6.6 if small else 7.5)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        padding_x = 4 if small else 6
        width = metrics.horizontalAdvance(text) + (padding_x * 2)
        height = 13 if small else 16
        badge_rect = QRectF(x, y, width, height)
        border = QColor(fg)
        border.setAlpha(44 if small else 58)
        painter.setPen(QPen(border, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(badge_rect, 7 if small else 8, 7 if small else 8)
        painter.setPen(fg)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)
        return int(badge_rect.right())
