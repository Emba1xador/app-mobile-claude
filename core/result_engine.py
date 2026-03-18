from __future__ import annotations

from dataclasses import dataclass

from core.entities import BetLine, BetSpec, ResultPrize, ResultSnapshot, WinnerHit
from core.enums import BetType, Flag, SlotPosition
from core.group_table import detect_group
from core.parser import expand_closure, milhar_iv_permutations, rotate_left, unique_permutations


@dataclass(slots=True)
class PrizeProjection:
    prize: ResultPrize
    left2: str
    middle2: str
    right2: str
    right3: str


def _prize_text(prize: ResultPrize) -> str:
    return f"{prize.label} pr\u00eamio"


def _slot_text(slot: SlotPosition) -> str:
    if slot == SlotPosition.LEFT:
        return "dezena inicial"
    if slot == SlotPosition.MIDDLE:
        return "dezena central"
    return "dezena final"


def build_result_snapshot(numbers: list[str]) -> ResultSnapshot:
    prizes: list[ResultPrize] = []
    for index, number in enumerate(numbers, start=1):
        prizes.append(ResultPrize(index, number, detect_group(number[-2:])))
    return ResultSnapshot(prizes=prizes)


def project_prizes(snapshot: ResultSnapshot) -> list[PrizeProjection]:
    return [
        PrizeProjection(
            prize=prize,
            left2=prize.milhar[:2],
            middle2=prize.milhar[1:3],
            right2=prize.milhar[2:],
            right3=prize.milhar[1:],
        )
        for prize in snapshot.prizes
    ]


def evaluate_line(line: BetLine, snapshot: ResultSnapshot | None) -> list[WinnerHit]:
    if snapshot is None or line.spec is None or not line.spec.is_valid:
        return []
    projections = project_prizes(snapshot)
    return evaluate_spec(line.spec, projections)


def evaluate_spec(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    match spec.bet_type:
        case BetType.CENTENA:
            return _evaluate_centena(spec, projections)
        case BetType.MILHAR_CENTENA:
            return _evaluate_mc(spec, projections)
        case BetType.MILHAR:
            return _evaluate_milhar(spec, projections)
        case BetType.DEZENA:
            return _evaluate_dezena(spec, projections)
        case BetType.DUQUE_DEZENA:
            return _evaluate_duque_terno(spec, projections, expected=2)
        case BetType.TERNO_DEZENA:
            return _evaluate_duque_terno(spec, projections, expected=3)
        case BetType.GRUPO:
            return _evaluate_grupo(spec, projections)
        case BetType.TERNO_GRUPO:
            return _evaluate_tg(spec, projections)
        case BetType.FECHAMENTO:
            return _evaluate_fechamento(spec, projections)
        case _:
            return []


def _evaluate_centena(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    base = spec.numbers[0]
    candidates = {base}
    if Flag.INVERTIDA in spec.flags:
        candidates = set(unique_permutations(base))
    winners: list[WinnerHit] = []
    for projection in projections:
        if projection.right3 in candidates:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.right3,
                    detail=f"Centena no {_prize_text(projection.prize)}",
                )
            )
        if Flag.DE in spec.flags and projection.prize.milhar[:3] in candidates:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.prize.milhar[:3],
                    detail=f"Centena DE no {_prize_text(projection.prize)}",
                )
            )
    return _dedupe_hits(winners)


def _evaluate_mc(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    base = spec.numbers[0]
    formations = [base]
    if Flag.INVERTIDA in spec.flags:
        formations = milhar_iv_permutations(base)
    candidate_centenas: set[str] = set()
    for formation in formations:
        candidate_centenas.add(formation[1:])
        if Flag.DE in spec.flags:
            candidate_centenas.add(rotate_left(formation)[1:])
    winners: list[WinnerHit] = []
    for projection in projections:
        if projection.right3 in candidate_centenas:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.right3,
                    detail=f"MC por centena no {_prize_text(projection.prize)}",
                )
            )
    return _dedupe_hits(winners)


def _evaluate_milhar(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    candidates = {spec.numbers[0]}
    if Flag.INVERTIDA in spec.flags:
        candidates = set(milhar_iv_permutations(spec.numbers[0]))
    winners: list[WinnerHit] = []
    for projection in projections:
        if projection.prize.milhar in candidates:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.prize.milhar,
                    detail=f"Milhar no {_prize_text(projection.prize)}",
                )
            )
    return winners


def _evaluate_dezena(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    target = spec.numbers[0]
    slots = [SlotPosition.RIGHT]
    if Flag.DE in spec.flags:
        slots = [SlotPosition.LEFT, SlotPosition.RIGHT]
    elif Flag.DEM in spec.flags:
        slots = [SlotPosition.LEFT, SlotPosition.MIDDLE, SlotPosition.RIGHT]
    winners: list[WinnerHit] = []
    for projection in projections:
        for slot in slots:
            value = _slot_value(projection, slot)
            if value == target:
                winners.append(
                    WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=value,
                    detail=f"Dezena na {_slot_text(slot)} do {_prize_text(projection.prize)}",
                )
            )
    return _dedupe_hits(winners)


def _evaluate_duque_terno(
    spec: BetSpec,
    projections: list[PrizeProjection],
    expected: int,
) -> list[WinnerHit]:
    values = set(spec.numbers)
    allowed_slots = [SlotPosition.RIGHT]
    if Flag.DE in spec.flags:
        allowed_slots = [SlotPosition.LEFT, SlotPosition.RIGHT]
    elif Flag.DEM in spec.flags:
        allowed_slots = [SlotPosition.LEFT, SlotPosition.MIDDLE, SlotPosition.RIGHT]
    winners: list[WinnerHit] = []
    for slot in allowed_slots:
        slot_values = {_slot_value(projection, slot) for projection in projections}
        if values.issubset(slot_values):
            winners.append(
                WinnerHit(
                    prize_index=0,
                    prize_label="GERAL",
                    match_value=", ".join(sorted(values)),
                    detail=f"{spec.bet_type.value} na {_slot_text(slot)}",
                )
            )
            break
    return winners if len(values) == expected else []


def _evaluate_grupo(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    target = int(spec.numbers[0])
    winners: list[WinnerHit] = []
    for projection in projections:
        if projection.prize.group == target:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=f"Grupo {target:02d}",
                    detail=f"Grupo no {_prize_text(projection.prize)}",
                )
            )
    return winners


def _evaluate_tg(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    targets = {int(number) for number in spec.numbers}
    groups = {projection.prize.group for projection in projections}
    if targets.issubset(groups):
        return [
            WinnerHit(
                prize_index=0,
                prize_label="GERAL",
                match_value=", ".join(f"{group:02d}" for group in sorted(targets)),
                detail="Terno de grupo presente no resultado",
            )
        ]
    return []


def _evaluate_fechamento(spec: BetSpec, projections: list[PrizeProjection]) -> list[WinnerHit]:
    start, end = spec.numbers
    candidates = set(expand_closure(start, end))
    if Flag.INVERTIDA in spec.flags:
        expanded: set[str] = set()
        for candidate in candidates:
            expanded.update(unique_permutations(candidate))
        candidates = expanded
    winners: list[WinnerHit] = []
    for projection in projections:
        if projection.right3 in candidates:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.right3,
                    detail=f"Fechamento por centena no {_prize_text(projection.prize)}",
                )
            )
        if Flag.DE in spec.flags and projection.prize.milhar[:3] in candidates:
            winners.append(
                WinnerHit(
                    prize_index=projection.prize.prize_index,
                    prize_label=projection.prize.label,
                    match_value=projection.prize.milhar[:3],
                    detail=f"Fechamento DE no {_prize_text(projection.prize)}",
                )
            )
    return _dedupe_hits(winners)


def _slot_value(projection: PrizeProjection, slot: SlotPosition) -> str:
    if slot == SlotPosition.LEFT:
        return projection.left2
    if slot == SlotPosition.MIDDLE:
        return projection.middle2
    return projection.right2


def _dedupe_hits(hits: list[WinnerHit]) -> list[WinnerHit]:
    seen: set[tuple[int, str, str]] = set()
    unique: list[WinnerHit] = []
    for hit in hits:
        key = (hit.prize_index, hit.match_value, hit.detail)
        if key not in seen:
            seen.add(key)
            unique.append(hit)
    return unique
