from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from urllib.parse import quote

from core.finance_engine import quantize_money

MONEY_PATTERN = re.compile(r"^(?P<sign>-?)(?P<integer>(?:\d+|\d{1,3}(?:\.\d{3})+))(?:,(?P<decimal>\d{1,2}))?$")


def format_money(value: Decimal | None) -> str:
    if value is None:
        return "--"
    normalized = quantize_money(value)
    text = f"{normalized:.2f}"
    return text.replace(".", ",")


def parse_money(text: str) -> Decimal | None:
    stripped = text.strip()
    if not stripped:
        return None
    match = MONEY_PATTERN.fullmatch(stripped)
    if match is None:
        raise ValueError("Valor inv\u00e1lido. Use o formato brasileiro, por exemplo: 1234,56.")
    integer_part = match.group("integer").replace(".", "")
    decimal_part = (match.group("decimal") or "00").ljust(2, "0")
    normalized = f"{match.group('sign')}{integer_part}.{decimal_part}"
    try:
        return quantize_money(Decimal(normalized))
    except InvalidOperation as exc:
        raise ValueError("Valor inv\u00e1lido. Use o formato brasileiro, por exemplo: 1234,56.") from exc


def format_percentage(value: Decimal) -> str:
    percent = quantize_money(value * Decimal("100"))
    return f"{percent:.2f}".rstrip("0").rstrip(".").replace(".", ",") + "%"


def encode_whatsapp_message(message: str) -> str:
    return quote(message, safe="")


def sanitize_phone(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    if digits.startswith("55") and len(digits) in {12, 13}:
        return digits[2:]
    return digits
