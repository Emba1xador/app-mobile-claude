from __future__ import annotations

import re
import unicodedata
from itertools import permutations

from core.entities import BetSpec
from core.enums import BetType, CommitMode, Flag
from core.validators import ensure_numeric, error_spec, validate_flags


FLAG_ALIASES = {
    "IV": Flag.INVERTIDA,
    "I.V": Flag.INVERTIDA,
    "DE": Flag.DE,
    "DEM": Flag.DEM,
}

TYPE_BY_PREFIX = {
    "C": BetType.CENTENA,
    "MC": BetType.MILHAR_CENTENA,
    "M": BetType.MILHAR,
    "D": BetType.DEZENA,
    "DD": BetType.DUQUE_DEZENA,
    "TD": BetType.TERNO_DEZENA,
    "G": BetType.GRUPO,
    "TG": BetType.TERNO_GRUPO,
    "F": BetType.FECHAMENTO,
}


def _normalize_space(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().upper())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _normalize_compact_aliases(text: str) -> str:
    compact = text.replace(" ", "")
    closure_match = re.fullmatch(r"(?:F)?(\d{3})(?:/|A)(\d{3})(?:F)?", compact)
    if closure_match:
        start, end = closure_match.groups()
        return f"F {start} / {end}"
    tg_match = re.fullmatch(r"TG(\d{1,2})/(\d{1,2})/(\d{1,2})", compact)
    if tg_match:
        first, second, third = tg_match.groups()
        return f"TG {first} {second} {third}"
    if re.fullmatch(r"D\d{2}", compact):
        return f"D {compact[1:]}"
    if re.fullmatch(r"/\d{2}", compact):
        return f"D {compact[1:]}"
    if re.fullmatch(r"G\d{1,2}", compact):
        return f"G {compact[1:]}"
    return text


def _extract_flags(tokens: list[str]) -> tuple[list[str], list[Flag]]:
    clean_tokens: list[str] = []
    flags: list[Flag] = []
    for token in tokens:
        mapped = FLAG_ALIASES.get(token)
        if mapped:
            flags.append(mapped)
        else:
            clean_tokens.append(token)
    return clean_tokens, flags


def format_spec(spec: BetSpec) -> str:
    if spec.bet_type == BetType.ERROR:
        return "ERRO"
    if spec.bet_type == BetType.FECHAMENTO and len(spec.numbers) == 2:
        flags = f" {' '.join(flag.value for flag in spec.flags)}" if spec.flags else ""
        return f"F {spec.numbers[0]} / {spec.numbers[1]}{flags}".strip()
    numbers = " ".join(spec.numbers)
    flags = f" {' '.join(flag.value for flag in spec.flags)}" if spec.flags else ""
    return f"{spec.bet_type.value} {numbers}{flags}".strip()


def _parse_closure(raw_text: str, flags: list[Flag]) -> BetSpec:
    match = re.search(r"(\d{3})\s*(?:/|A)\s*(\d{3})", _normalize_space(raw_text))
    if not match:
        return error_spec(raw_text, "Fechamento inv\u00e1lido.")
    start, end = match.groups()
    if not ensure_numeric(start, 3) or not ensure_numeric(end, 3):
        return error_spec(raw_text, "Fechamento deve usar centenas de 3 digitos.")
    error = validate_flags(BetType.FECHAMENTO, flags)
    if error:
        return error_spec(raw_text, error)
    spec = BetSpec(BetType.FECHAMENTO, [start, end], flags=flags, raw_text=raw_text)
    spec.normalized_text = format_spec(spec)
    return spec


def parse_bet_input(raw_text: str, commit_mode: CommitMode = CommitMode.ENTER) -> BetSpec | None:
    normalized = _normalize_compact_aliases(_normalize_space(raw_text))
    if not normalized:
        return None
    if re.fullmatch(r"\d{2}/", slash_compact):
        normalized = f"D {slash_compact[:2]}"
    elif re.fullmatch(r"\d{2}/\d{2}", slash_compact):
        normalized = f"DD {slash_compact.replace('/', ' ')}"
    elif re.fullmatch(r"\d{2}/\d{2}/\d{2}", slash_compact):
        normalized = f"TD {slash_compact.replace('/', ' ')}"
    elif re.fullmatch(r"\d{3}/\d{3}", slash_compact):
        normalized = f"F {slash_compact.replace('/', ' / ')}"

    tokens = normalized.split(" ")
    tokens, flags = _extract_flags(tokens)
    if not tokens:
        return None
    candidate_text = " ".join(tokens)
    if re.search(r"\d{3}\s*(?:/|A)\s*\d{3}", candidate_text):
        return _parse_closure(candidate_text, flags)

    if len(tokens) == 1 and ensure_numeric(tokens[0], 3):
        spec = BetSpec(BetType.CENTENA, [tokens[0]], flags=flags, raw_text=raw_text)
    elif len(tokens) == 1 and ensure_numeric(tokens[0], 4):
        bet_type = BetType.MILHAR_CENTENA if commit_mode == CommitMode.SHIFT_MC else BetType.MILHAR
        spec = BetSpec(bet_type, [tokens[0]], flags=flags, raw_text=raw_text)
    else:
        prefix = tokens[0]
        suffix = tokens[-1]
        if prefix == "F" or suffix == "F" or re.search(r"\d{3}\s*(?:/|A)\s*\d{3}", normalized):
            return _parse_closure(normalized, flags)
        if prefix in TYPE_BY_PREFIX:
            bet_type = TYPE_BY_PREFIX[prefix]
            number_tokens = tokens[1:]
        elif suffix in TYPE_BY_PREFIX:
            bet_type = TYPE_BY_PREFIX[suffix]
            number_tokens = tokens[:-1]
        else:
            return error_spec(raw_text)
        spec = BetSpec(bet_type, number_tokens, flags=flags, raw_text=raw_text)

    error = _validate_spec(spec)
    if error:
        return error_spec(raw_text, error)
    spec.normalized_text = format_spec(spec)
    return spec


def _validate_spec(spec: BetSpec) -> str | None:
    error = validate_flags(spec.bet_type, spec.flags)
    if error:
        return error
    numbers = spec.numbers
    bet_type = spec.bet_type
    if bet_type == BetType.CENTENA and (len(numbers) != 1 or not ensure_numeric(numbers[0], 3)):
        return "Centena inv\u00e1lida."
    if bet_type == BetType.MILHAR_CENTENA and (len(numbers) != 1 or not ensure_numeric(numbers[0], 4)):
        return "MC inv\u00e1lida."
    if bet_type == BetType.MILHAR and (len(numbers) != 1 or not ensure_numeric(numbers[0], 4)):
        return "Milhar inv\u00e1lida."
    if bet_type == BetType.DEZENA and (len(numbers) != 1 or not ensure_numeric(numbers[0], 2)):
        return "Dezena inv\u00e1lida."
    if bet_type == BetType.DUQUE_DEZENA and (
        len(numbers) != 2 or any(not ensure_numeric(number, 2) for number in numbers)
    ):
        return "Duque de dezena inv\u00e1lido."
    if bet_type == BetType.TERNO_DEZENA and (
        len(numbers) != 3 or any(not ensure_numeric(number, 2) for number in numbers)
    ):
        return "Terno de dezena inv\u00e1lido."
    if bet_type == BetType.GRUPO:
        if len(numbers) != 1 or not numbers[0].isdigit():
            return "Grupo inv\u00e1lido."
        number = int(numbers[0])
        if not 1 <= number <= 25:
            return "Grupo deve estar entre 1 e 25."
        spec.numbers = [f"{number:02d}"]
    if bet_type == BetType.TERNO_GRUPO:
        if len(numbers) != 3 or any(not token.isdigit() for token in numbers):
            return "Terno de grupo inv\u00e1lido."
        groups = [int(token) for token in numbers]
        if any(group < 1 or group > 25 for group in groups):
            return "Grupo deve estar entre 1 e 25."
        spec.numbers = [str(group) for group in groups]
    if bet_type == BetType.FECHAMENTO:
        start, end = numbers
        if not ensure_numeric(start, 3) or not ensure_numeric(end, 3):
            return "Fechamento deve usar centenas de 3 d\u00edgitos."
        if int(start) > int(end):
            return "Fechamento com intervalo inv\u00e1lido."
    return None


def rotate_left(number: str) -> str:
    return number[1:] + number[0]


def unique_permutations(number: str) -> list[str]:
    return sorted({"".join(item) for item in permutations(number)})


def milhar_iv_permutations(number: str) -> list[str]:
    first = number[0]
    others = number[1:]
    result: set[str] = set()
    for perm in set(permutations(others)):
        middle = "".join(perm)
        result.add(first + middle)
        result.add(middle + first)
    return sorted(result)


def expand_closure(start: str, end: str) -> list[str]:
    start_value = int(start)
    end_value = int(end)
    # Fechamento 000/999 usa passo 111 para gerar apenas as centenas-espelho (000, 111, 222, ..., 999)
    step = 111 if start == "000" and end == "999" else 100
    values = list(range(start_value, end_value + 1, step))
    return [f"{value:03d}" for value in values]
