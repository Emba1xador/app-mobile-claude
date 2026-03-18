from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class UiState:
    geometry: str | None = None
    window_state: str | None = None
    splitter_state: str | None = None
    selected_block_id: str | None = None
    selected_page_id: str | None = None
    selected_line_id: str | None = None
    selected_column: int = 0
    extra: dict[str, Any] = field(default_factory=dict)
