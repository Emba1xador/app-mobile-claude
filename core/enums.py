from __future__ import annotations

from enum import Enum


class BetType(str, Enum):
    CENTENA = "C"
    MILHAR_CENTENA = "MC"
    MILHAR = "M"
    DEZENA = "D"
    DUQUE_DEZENA = "DD"
    TERNO_DEZENA = "TD"
    GRUPO = "G"
    TERNO_GRUPO = "TG"
    FECHAMENTO = "F"
    ERROR = "ERRO"


class Flag(str, Enum):
    INVERTIDA = "I.V"
    DE = "DE"
    DEM = "DEM"


class CommitMode(str, Enum):
    ENTER = "enter"
    SHIFT_MC = "shift_mc"


class RowType(str, Enum):
    BLOCK_HEADER = "block_header"
    PAGE_HEADER = "page_header"
    BET_ENTRY = "bet_entry"


class SlotPosition(str, Enum):
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"
