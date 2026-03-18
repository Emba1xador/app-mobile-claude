from __future__ import annotations

from dataclasses import dataclass

from core.entities import Page


@dataclass(slots=True)
class PageLockedError(Exception):
    page_id: str
    page_number: int
    block_number: str
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(slots=True)
class BlockLockedError(Exception):
    block_id: str
    block_number: str
    message: str

    def __str__(self) -> str:
        return self.message


def is_page_locked(page: Page) -> bool:
    return page.has_any_value
