from __future__ import annotations

from PySide6.QtCore import QPoint, QTimer, Qt, QRect, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QAbstractItemDelegate, QAbstractItemView, QHeaderView, QTableView

from core.page_lock import BlockLockedError
from ui.models.finance_table_model import FinanceTableModel
from ui.theme import COLOR_TOKENS, color, tinted


class FinanceHeaderView(QHeaderView):
    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setObjectName("financeHeader")
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSectionsClickable(False)
        self.setHighlightSections(False)
        self.setFixedHeight(40)

    def sizeHint(self):  # noqa: N802
        size = super().sizeHint()
        size.setHeight(40)
        return size

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.fillRect(self.rect(), color("panel_bg"))
        model = self.model()
        if model is None:
            return

        header_font = QFont(self.font())
        header_font.setPointSizeF(8.15)
        header_font.setBold(True)
        painter.setFont(header_font)

        for column in range(model.columnCount()):
            if self.isSectionHidden(column):
                continue
            x = self.sectionViewportPosition(column)
            width = self.sectionSize(column)
            section_rect = QRect(x, 0, width, self.height())
            painter.setPen(color("text_muted"))
            alignment = Qt.AlignmentFlag.AlignCenter
            if column == FinanceTableModel.COL_BLOCK:
                alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            elif column != FinanceTableModel.COL_CONTACT:
                alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            painter.drawText(
                section_rect.adjusted(12, 0, -12, 0),
                alignment,
                str(model.headerData(column, Qt.Orientation.Horizontal) or ""),
            )

        painter.setPen(QPen(tinted("divider", 148), 1))
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())


class FinanceTableView(QTableView):
    contactMenuRequested = Signal(str, object)
    blockNavigationRequested = Signal(str)
    lockConflict = Signal(object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHorizontalHeader(FinanceHeaderView(self))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.horizontalHeader().setMinimumSectionSize(48)
        header_font = QFont(self.horizontalHeader().font())
        header_font.setPointSizeF(8.3)
        self.horizontalHeader().setFont(header_font)
        cell_font = QFont(self.font())
        cell_font.setPointSizeF(10.45)
        self.setFont(cell_font)

    def setModel(self, model) -> None:  # noqa: N802
        super().setModel(model)
        QTimer.singleShot(0, self._resize_columns_to_viewport)

    def mousePressEvent(self, event) -> None:
        index = self.indexAt(event.position().toPoint())
        row = None
        if index.isValid():
            row = self.model().row_at(index.row())
            if index.column() == FinanceTableModel.COL_CONTACT:
                super().mousePressEvent(event)
                anchor = self.viewport().mapToGlobal(self.visualRect(index).bottomLeft())
                self.contactMenuRequested.emit(row.block_id, anchor)
                return
        super().mousePressEvent(event)
        if index.isValid() and row is not None and index.column() == FinanceTableModel.COL_BLOCK:
            self.blockNavigationRequested.emit(row.block_id)

    def commit_finance_editor(self, editor) -> None:
        index = self.currentIndex()
        if not index.isValid():
            return
        payload = {"text": editor.text()}
        if self.model().setData(index, payload, Qt.ItemDataRole.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
            return
        exc = self.model().last_exception
        if isinstance(exc, BlockLockedError):
            self.lockConflict.emit(exc, lambda: self.retry_commit(index, editor))
            return
        editor.selectAll()

    def retry_commit(self, index, editor) -> None:
        payload = {"text": editor.text(), "force_unlock": True}
        if self.model().setData(index, payload, Qt.ItemDataRole.EditRole):
            self.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)
            return
        editor.selectAll()

    def editing_block_id(self) -> str | None:
        if self.state() != QAbstractItemView.State.EditingState:
            return None
        index = self.currentIndex()
        if not index.isValid():
            return None
        row = self.model().row_at(index.row())
        return row.block_id

    def focus_block(self, block_id: str, column: int = FinanceTableModel.COL_BLOCK) -> bool:
        for row_index in range(self.model().rowCount()):
            row = self.model().row_at(row_index)
            if row.block_id != block_id:
                continue
            target_index = self.model().index(row_index, column)
            self.setCurrentIndex(target_index)
            self.selectRow(row_index)
            self.scrollTo(target_index)
            return True
        return False

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._resize_columns_to_viewport()

    def drawRow(self, painter: QPainter, option, index) -> None:  # noqa: N802
        super().drawRow(painter, option, index)
        selected = self.selectionModel() is not None and self.selectionModel().isRowSelected(index.row(), index.parent())
        painter.save()
        if selected:
            row_rect = option.rect.adjusted(6, 4, -6, -4)
            overlay = QColor(color("focus"))
            overlay.setAlpha(20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(overlay)
            painter.drawRoundedRect(row_rect, 10, 10)

            accent = QColor(color("focus_strong"))
            accent.setAlpha(200)
            painter.fillRect(row_rect.left() + 3, row_rect.top() + 5, 3, row_rect.height() - 10, accent)

        painter.setPen(QPen(tinted("divider", 40), 0.5))
        painter.drawLine(option.rect.bottomLeft() + QPoint(10, 0), option.rect.bottomRight() - QPoint(10, 0))
        painter.restore()

    def _resize_columns_to_viewport(self) -> None:
        model = self.model()
        if model is None or self.viewport().width() <= 0:
            return

        available_width = self.viewport().width() - 2
        header_metrics = QFontMetrics(self.horizontalHeader().font())
        cell_metrics = QFontMetrics(self.font())

        widths = {
            FinanceTableModel.COL_CONTACT: 82,
        }

        flex_columns = (
            FinanceTableModel.COL_BLOCK,
            FinanceTableModel.COL_RECEIVED,
            FinanceTableModel.COL_BRUTO,
            FinanceTableModel.COL_LIQUIDO,
            FinanceTableModel.COL_SALDO,
        )

        minimums = {
            FinanceTableModel.COL_BLOCK: self._column_min_width(
                FinanceTableModel.COL_BLOCK,
                header_metrics,
                cell_metrics,
                floor=78,
                padding=18,
            ),
            FinanceTableModel.COL_RECEIVED: self._column_min_width(
                FinanceTableModel.COL_RECEIVED,
                header_metrics,
                cell_metrics,
                floor=92,
                padding=16,
            ),
            FinanceTableModel.COL_BRUTO: self._column_min_width(
                FinanceTableModel.COL_BRUTO,
                header_metrics,
                cell_metrics,
                floor=86,
                padding=16,
            ),
            FinanceTableModel.COL_LIQUIDO: self._column_min_width(
                FinanceTableModel.COL_LIQUIDO,
                header_metrics,
                cell_metrics,
                floor=126,
                padding=16,
            ),
            FinanceTableModel.COL_SALDO: self._column_min_width(
                FinanceTableModel.COL_SALDO,
                header_metrics,
                cell_metrics,
                floor=96,
                padding=16,
            ),
        }

        weights = {
            FinanceTableModel.COL_BLOCK: 13,
            FinanceTableModel.COL_RECEIVED: 14,
            FinanceTableModel.COL_BRUTO: 11,
            FinanceTableModel.COL_LIQUIDO: 15,
            FinanceTableModel.COL_SALDO: 13,
        }

        base_total = sum(widths.values()) + sum(minimums[column] for column in flex_columns)
        extra_space = max(0, available_width - base_total)
        total_weight = sum(weights.values())

        for column in flex_columns:
            widths[column] = minimums[column] + round(extra_space * weights[column] / total_weight)

        allocated = sum(widths.values())
        if allocated > available_width:
            self._shrink_numeric_columns(widths, allocated - available_width)
        elif allocated < available_width:
            widths[FinanceTableModel.COL_LIQUIDO] += available_width - allocated

        for column, width in widths.items():
            self.setColumnWidth(column, max(48, width))

    def _column_min_width(
        self,
        column: int,
        header_metrics: QFontMetrics,
        cell_metrics: QFontMetrics,
        floor: int,
        padding: int,
    ) -> int:
        header_text = str(self.model().headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) or "")
        candidates = [header_metrics.horizontalAdvance(header_text)]
        for row_index in range(self.model().rowCount()):
            cell_text = str(self.model().index(row_index, column).data() or "")
            if cell_text:
                candidates.append(cell_metrics.horizontalAdvance(cell_text))
        return max(floor, max(candidates, default=0) + padding)

    def _shrink_numeric_columns(self, widths: dict[int, int], overflow: int) -> None:
        shrink_order = [
            (FinanceTableModel.COL_LIQUIDO, 112),
            (FinanceTableModel.COL_RECEIVED, 84),
            (FinanceTableModel.COL_SALDO, 80),
            (FinanceTableModel.COL_BRUTO, 76),
            (FinanceTableModel.COL_BLOCK, 64),
        ]
        remaining = overflow
        while remaining > 0:
            changed = False
            for column, floor in shrink_order:
                if widths[column] > floor:
                    widths[column] -= 1
                    remaining -= 1
                    changed = True
                    if remaining == 0:
                        break
            if not changed:
                break
