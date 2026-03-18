from decimal import Decimal

import pytest

from services.formatting import parse_money


def test_parse_money_accepts_brazilian_format():
    assert parse_money("1.234") == Decimal("1234.00")
    assert parse_money("1.234,56") == Decimal("1234.56")
    assert parse_money("1234,56") == Decimal("1234.56")
    assert parse_money("1234") == Decimal("1234.00")
    assert parse_money("10,5") == Decimal("10.50")


def test_parse_money_rejects_ambiguous_or_invalid_input():
    with pytest.raises(ValueError):
        parse_money("1,234")

    with pytest.raises(ValueError):
        parse_money("12.34")

    with pytest.raises(ValueError):
        parse_money("abc")
