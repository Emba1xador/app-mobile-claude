from __future__ import annotations

from core.enums import CommitMode, RowType
from services.controller import BancaController


def test_projection_marks_trailing_blank_and_count(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("524")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    rows = controller.get_projection()

    block_header = rows[0]
    page_header = next(row for row in rows if row.row_type == RowType.PAGE_HEADER)
    trailing_blank = next(row for row in rows if row.row_type == RowType.BET_ENTRY and row.is_trailing_blank)

    assert block_header.row_type == RowType.BLOCK_HEADER
    assert page_header.left_text == "Página 1"
    assert page_header.right_text.startswith("R$ ")
    assert trailing_blank.left_text == "+ Nova aposta"
    assert trailing_blank.is_trailing_blank is True


def test_projection_marks_even_pages(tmp_path):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("524")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.create_page_after(page_id)

    rows = controller.get_projection()
    even_page_rows = [row for row in rows if row.page_number == 2]

    assert even_page_rows
    assert all(row.page_is_even for row in even_page_rows)
