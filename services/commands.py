from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SelectionContext:
    block_id: str | None = None
    page_id: str | None = None
    line_id: str | None = None
    column: int = 0
