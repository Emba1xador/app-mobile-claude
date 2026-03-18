from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app_state.ui_state import UiState
from core.entities import Block, ResultSnapshot


@dataclass(slots=True)
class AppState:
    version: int = 1
    blocks: list[Block] = field(default_factory=list)
    result: ResultSnapshot | None = None
    percentage: Decimal = Decimal("0.70")
    session_name: str = ""
    total_paid_prizes: Decimal | None = None
    session_notes: str = ""
    whatsapp_map: dict[str, str] = field(default_factory=dict)
    ui_state: UiState = field(default_factory=UiState)
