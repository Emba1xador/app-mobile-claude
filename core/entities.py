from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from core.enums import BetType, Flag, RowType


def make_id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class BetSpec:
    bet_type: BetType
    numbers: list[str]
    flags: list[Flag] = field(default_factory=list)
    raw_text: str = ""
    normalized_text: str = ""
    error_message: str | None = None

    @property
    def is_error(self) -> bool:
        return self.bet_type == BetType.ERROR

    @property
    def is_valid(self) -> bool:
        return not self.is_error


@dataclass(slots=True)
class WinnerHit:
    prize_index: int
    prize_label: str
    match_value: str
    detail: str


@dataclass(slots=True)
class BetLine:
    line_id: str
    raw_text: str = ""
    spec: BetSpec | None = None
    value: Decimal | None = None
    winners: list[WinnerHit] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.raw_text.strip() and self.spec is None

    @property
    def is_error(self) -> bool:
        return self.spec is not None and self.spec.is_error

    @property
    def is_valid_bet(self) -> bool:
        return self.spec is not None and self.spec.is_valid


@dataclass(slots=True)
class Page:
    page_id: str
    number: int
    lines: list[BetLine] = field(default_factory=list)

    @property
    def has_any_value(self) -> bool:
        return any(line.is_valid_bet and line.value is not None for line in self.lines)


@dataclass(slots=True)
class Block:
    block_id: str
    number: str
    pages: list[Page] = field(default_factory=list)
    money_received: Decimal | None = None
    whatsapp_phone: str | None = None
    money_locked: bool = False
    money_fiado: bool = False  # "a prazo/fiado" — sem valor numérico mas marcado


@dataclass(slots=True)
class ResultPrize:
    prize_index: int
    milhar: str
    group: int

    @property
    def label(self) -> str:
        return f"{self.prize_index}\u00b0"


@dataclass(slots=True)
class ResultSnapshot:
    prizes: list[ResultPrize] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return len(self.prizes) == 5 and all(len(prize.milhar) == 4 for prize in self.prizes)


@dataclass(slots=True)
class FinanceRow:
    block_id: str
    block_number: str
    bruto: Decimal
    percentage: Decimal
    liquido: Decimal
    money_received: Decimal | None
    resultado: Decimal | None
    whatsapp_phone: str | None
    has_winner: bool
    values_complete: bool
    money_locked: bool
    winner_count: int = 0
    money_fiado: bool = False


@dataclass(slots=True)
class SummaryLine:
    text: str
    tone: str = "neutral"
    kind: str = "item"
    indent: int = 0


@dataclass(slots=True)
class ProjectionRow:
    row_type: RowType
    block_id: str
    page_id: str
    line_id: str | None
    block_number: str
    page_number: int
    left_text: str
    right_text: str
    line_ref: BetLine | None = None
    page_ref: Page | None = None
    page_is_even: bool = False
    block_is_even: bool = False
    bet_row_is_even: bool = False
    valid_bet_count: int = 0
    is_trailing_blank: bool = False
    ghost_value_hint: str = ""
    block_page_count: int = 0
    block_bet_count: int = 0
    block_prize_count: int = 0
    block_pendency_count: int = 0


