from decimal import Decimal

from core.entities import BetLine, BetSpec, Block, Page, make_id
from core.enums import BetType
from core.finance_engine import block_total, finance_row, page_total


def build_block() -> Block:
    page = Page(
        page_id=make_id(),
        number=1,
        lines=[
            BetLine(
                line_id=make_id(),
                spec=BetSpec(bet_type=BetType.CENTENA, numbers=["555"]),
                value=Decimal("2.00"),
            ),
            BetLine(
                line_id=make_id(),
                spec=BetSpec(bet_type=BetType.CENTENA, numbers=["666"]),
                value=Decimal("3.50"),
            ),
        ],
    )
    return Block(block_id=make_id(), number="452", pages=[page], money_received=Decimal("5.00"))


def test_page_and_block_totals():
    block = build_block()
    assert page_total(block.pages[0].lines) == Decimal("5.50")
    assert block_total(block) == Decimal("5.50")


def test_finance_result():
    block = build_block()
    row = finance_row(block, Decimal("0.70"))
    assert row.bruto == Decimal("5.50")
    assert row.liquido == Decimal("3.85")
    assert row.resultado == Decimal("1.15")


def test_totals_ignore_invalid_lines():
    page = Page(
        page_id=make_id(),
        number=1,
        lines=[
            BetLine(
                line_id=make_id(),
                spec=BetSpec(bet_type=BetType.CENTENA, numbers=["555"]),
                value=Decimal("2.00"),
            ),
            BetLine(line_id=make_id(), value=Decimal("8.00")),
        ],
    )
    block = Block(block_id=make_id(), number="452", pages=[page], money_received=Decimal("10.00"))

    assert page_total(page.lines) == Decimal("2.00")
    assert block_total(block) == Decimal("2.00")
    assert page.has_any_value is True
