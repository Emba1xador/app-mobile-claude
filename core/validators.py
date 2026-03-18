from __future__ import annotations

from core.entities import BetSpec
from core.enums import BetType, Flag


def validate_flags(bet_type: BetType, flags: list[Flag]) -> str | None:
    unique_flags = list(dict.fromkeys(flags))
    if len(unique_flags) != len(flags):
        return "Flag repetida."
    if Flag.INVERTIDA in flags and bet_type in {
        BetType.DEZENA,
        BetType.DUQUE_DEZENA,
        BetType.TERNO_DEZENA,
        BetType.GRUPO,
        BetType.TERNO_GRUPO,
    }:
        return "I.V inv\u00e1lido para este tipo."
    if Flag.DEM in flags and bet_type not in {
        BetType.DEZENA,
        BetType.DUQUE_DEZENA,
        BetType.TERNO_DEZENA,
    }:
        return "DEM inv\u00e1lido para este tipo."
    if Flag.DE in flags and Flag.DEM in flags and bet_type in {
        BetType.DEZENA,
        BetType.DUQUE_DEZENA,
        BetType.TERNO_DEZENA,
    }:
        return "DE e DEM n\u00e3o podem coexistir."
    if Flag.DE in flags and bet_type in {BetType.GRUPO, BetType.TERNO_GRUPO}:
        return "DE inv\u00e1lido para este tipo."
    return None


def ensure_numeric(token: str, size: int) -> bool:
    return token.isdigit() and len(token) == size


def error_spec(raw_text: str, message: str = "Entrada inv\u00e1lida.") -> BetSpec:
    return BetSpec(
        bet_type=BetType.ERROR,
        numbers=[],
        raw_text=raw_text,
        normalized_text="ERRO",
        error_message=message,
    )
