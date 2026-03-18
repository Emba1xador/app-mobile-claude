from __future__ import annotations

from core.entities import BetLine, Block, Page, ProjectionRow
from core.enums import BetType, RowType
from core.finance_engine import page_total


def _bet_count_label(count: int) -> str:
    return "1 aposta" if count == 1 else f"{count} apostas"


def _page_count_label(count: int) -> str:
    return "1 p\u00e1g" if count == 1 else f"{count} p\u00e1g"


def _prize_count_label(count: int) -> str:
    return "1 pr\u00eamio" if count == 1 else f"{count} pr\u00eamios"


def _pendency_count_label(count: int) -> str:
    return "1 pend\u00eancia" if count == 1 else f"{count} pend\u00eancias"


def build_bets_projection(
    blocks: list[Block],
    *,
    filter_mode: str = "all",
    selected_block_id: str | None = None,
    selected_page_id: str | None = None,
    expanded_block_ids: set[str] | None = None,
) -> list[ProjectionRow]:
    expanded_block_ids = set(expanded_block_ids or {block.block_id for block in blocks})
    rows: list[ProjectionRow] = []
    for block_index, block in enumerate(blocks):
        metrics = _block_metrics(block)
        visible_pages = _visible_pages(block, filter_mode=filter_mode, selected_page_id=selected_page_id)
        if not _block_matches_filter(
            block,
            filter_mode=filter_mode,
            selected_block_id=selected_block_id,
            metrics=metrics,
            visible_pages=visible_pages,
        ):
            continue

        block_is_even = block_index % 2 == 1
        rows.append(
            ProjectionRow(
                row_type=RowType.BLOCK_HEADER,
                block_id=block.block_id,
                page_id="",
                line_id=None,
                block_number=block.number,
                page_number=0,
                left_text=f"Bloco {block.number}",
                right_text=_block_summary_text(
                    block,
                    metrics=metrics,
                    is_current=block.block_id == selected_block_id,
                ),
                block_is_even=block_is_even,
                block_page_count=metrics["page_count"],
                block_bet_count=metrics["bet_count"],
                block_prize_count=metrics["prize_count"],
                block_pendency_count=metrics["pendency_count"],
            )
        )

        if block.block_id not in expanded_block_ids:
            continue

        for page in visible_pages:
            valid_bet_count = sum(1 for line in page.lines if line.is_valid_bet)
            trailing_blank_id = _trailing_blank_line_id(page)
            page_total_text = f"R$ {page_total(page.lines):.2f}".replace(".", ",")
            rows.append(
                ProjectionRow(
                    row_type=RowType.PAGE_HEADER,
                    block_id=block.block_id,
                    page_id=page.page_id,
                    line_id=None,
                    block_number=block.number,
                    page_number=page.number,
                    left_text=f"P\u00e1gina {page.number}",
                    right_text=page_total_text,
                    page_ref=page,
                    page_is_even=page.number % 2 == 0,
                    block_is_even=block_is_even,
                    valid_bet_count=valid_bet_count,
                )
            )

            bet_row_index = 0
            for line in page.lines:
                is_trailing_blank = line.line_id == trailing_blank_id
                if is_trailing_blank and filter_mode in {"awarded", "pending"}:
                    continue
                if filter_mode == "awarded" and not line.winners:
                    continue
                if filter_mode == "pending" and not _line_matches_pending(line):
                    continue

                rows.append(
                    ProjectionRow(
                        row_type=RowType.BET_ENTRY,
                        block_id=block.block_id,
                        page_id=page.page_id,
                        line_id=line.line_id,
                        block_number=block.number,
                        page_number=page.number,
                        left_text="+ Nova aposta" if is_trailing_blank else (line.spec.normalized_text if line.spec else line.raw_text),
                        right_text=_winner_text(line),
                        line_ref=line,
                        page_ref=page,
                        page_is_even=page.number % 2 == 0,
                        block_is_even=block_is_even,
                        bet_row_is_even=bet_row_index % 2 == 1,
                        valid_bet_count=valid_bet_count,
                        is_trailing_blank=is_trailing_blank,
                        ghost_value_hint=build_ghost_value_hint(line),
                    )
                )
                bet_row_index += 1
    return rows


def find_page(blocks: list[Block], page_id: str) -> tuple[Block, Page] | None:
    for block in blocks:
        for page in block.pages:
            if page.page_id == page_id:
                return block, page
    return None


def count_numbers_typed(blocks: list[Block]) -> int:
    return sum(1 for block in blocks for page in block.pages for line in page.lines if line.is_valid_bet)


def build_ghost_value_hint(line: BetLine) -> str:
    if not line.is_valid_bet or line.spec is None:
        return ""
    separator = " / " if len(line.spec.numbers) == 2 and line.spec.bet_type == BetType.FECHAMENTO else " "
    return separator.join(line.spec.numbers)


def _visible_pages(block: Block, *, filter_mode: str, selected_page_id: str | None) -> list[Page]:
    if filter_mode == "current":
        if selected_page_id is not None:
            return [page for page in block.pages if page.page_id == selected_page_id]
        return list(block.pages[:1])
    if filter_mode == "awarded":
        return [page for page in block.pages if any(line.winners for line in page.lines)]
    if filter_mode == "pending":
        return [page for page in block.pages if _page_has_pending(page)]
    return list(block.pages)


def _block_matches_filter(
    block: Block,
    *,
    filter_mode: str,
    selected_block_id: str | None,
    metrics: dict[str, int],
    visible_pages: list[Page],
) -> bool:
    if filter_mode == "current":
        if selected_block_id is not None:
            return block.block_id == selected_block_id and bool(visible_pages)
        return bool(visible_pages)
    if filter_mode == "awarded":
        return metrics["prize_count"] > 0 and bool(visible_pages)
    if filter_mode == "pending":
        return metrics["pendency_count"] > 0 and bool(visible_pages)
    return True


def _block_metrics(block: Block) -> dict[str, int]:
    page_count = len(block.pages)
    bet_count = 0
    prize_count = 0
    pending_pages = 0
    invalid_pages = 0

    for page in block.pages:
        valid_lines = [line for line in page.lines if line.is_valid_bet]
        bet_count += len(valid_lines)
        prize_count += sum(len(line.winners) for line in page.lines)
        if valid_lines and any(line.value is None for line in valid_lines):
            pending_pages += 1
        if any(line.is_error for line in page.lines):
            invalid_pages += 1

    pendency_count = pending_pages + invalid_pages
    if block.money_received is None:
        pendency_count += 1
    if not block.whatsapp_phone:
        pendency_count += 1
    if bet_count == 0:
        pendency_count += 1

    return {
        "page_count": page_count,
        "bet_count": bet_count,
        "prize_count": prize_count,
        "pending_pages": pending_pages,
        "invalid_pages": invalid_pages,
        "pendency_count": pendency_count,
    }


def _block_summary_text(block: Block, *, metrics: dict[str, int], is_current: bool) -> str:
    summary_parts = [_page_count_label(metrics["page_count"])]
    summary_parts.append(_bet_count_label(metrics["bet_count"]) if metrics["bet_count"] > 0 else "sem apostas")
    if is_current:
        summary_parts.append("em edi\u00e7\u00e3o")
    elif metrics["prize_count"] > 0:
        summary_parts.append(_prize_count_label(metrics["prize_count"]))
    elif metrics["pendency_count"] > 0:
        summary_parts.append(_pendency_count_label(metrics["pendency_count"]))
    return " \u2022 ".join(summary_parts)


def _page_has_pending(page: Page) -> bool:
    valid_lines = [line for line in page.lines if line.is_valid_bet]
    if not valid_lines:
        return True
    if any(line.value is None for line in valid_lines):
        return True
    if any(line.is_error for line in page.lines):
        return True
    return False


def _line_matches_pending(line: BetLine) -> bool:
    if line.is_empty:
        return True
    if line.is_error:
        return True
    if line.is_valid_bet and line.value is None:
        return True
    return False


def _winner_text(line: BetLine) -> str:
    if not line.winners:
        return ""
    winner = line.winners[0]
    return winner.detail if winner.prize_label == "GERAL" else f"{winner.prize_label} pr\u00eamio"


def _trailing_blank_line_id(page: Page) -> str | None:
    if not page.lines:
        return None
    last_line = page.lines[-1]
    if last_line.is_empty:
        return last_line.line_id
    return None
