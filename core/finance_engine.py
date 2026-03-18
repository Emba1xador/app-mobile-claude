from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.entities import Block, FinanceRow

CENT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def page_total(lines) -> Decimal:
    total = Decimal("0")
    for line in lines:
        if line.is_valid_bet and line.value is not None:
            total += line.value
    return quantize_money(total)


def block_total(block: Block) -> Decimal:
    total = Decimal("0")
    for page in block.pages:
        total += page_total(page.lines)
    return quantize_money(total)


def valid_bet_lines(block: Block):
    return [line for page in block.pages for line in page.lines if line.is_valid_bet]


def block_value_progress(block: Block) -> tuple[int, int]:
    valid_lines = valid_bet_lines(block)
    total = len(valid_lines)
    filled = sum(1 for line in valid_lines if line.value is not None)
    return filled, total


def block_values_complete(block: Block) -> bool:
    filled, total = block_value_progress(block)
    return total > 0 and filled == total


def winner_count(block: Block) -> int:
    return sum(1 for page in block.pages for line in page.lines if line.winners)


def finance_row(block: Block, percentage: Decimal, has_winner: bool = False) -> FinanceRow:
    bruto = block_total(block)
    liquido = quantize_money(bruto * percentage)
    resultado = None
    if block.money_received is not None:
        resultado = quantize_money(block.money_received - liquido)
    values_complete = block_values_complete(block)
    return FinanceRow(
        block_id=block.block_id,
        block_number=block.number,
        bruto=bruto,
        percentage=percentage,
        liquido=liquido,
        money_received=block.money_received,
        resultado=resultado,
        whatsapp_phone=block.whatsapp_phone,
        has_winner=has_winner,
        values_complete=values_complete,
        money_locked=block.money_locked,
        winner_count=winner_count(block),
    )
