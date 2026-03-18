from __future__ import annotations

from decimal import Decimal

from app_state.session import AppState
from app_state.ui_state import UiState
from core.entities import BetLine, BetSpec, Block, Page, ResultPrize, ResultSnapshot
from core.enums import BetType, Flag


def decimal_to_str(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def spec_to_dict(spec: BetSpec | None) -> dict | None:
    if spec is None:
        return None
    return {
        "bet_type": spec.bet_type.value,
        "numbers": spec.numbers,
        "flags": [flag.value for flag in spec.flags],
        "raw_text": spec.raw_text,
        "normalized_text": spec.normalized_text,
        "error_message": spec.error_message,
    }


def line_to_dict(line: BetLine) -> dict:
    return {
        "line_id": line.line_id,
        "raw_text": line.raw_text,
        "spec": spec_to_dict(line.spec),
        "value": decimal_to_str(line.value),
    }


def page_to_dict(page: Page) -> dict:
    return {
        "page_id": page.page_id,
        "number": page.number,
        "lines": [line_to_dict(line) for line in page.lines],
    }


def block_to_dict(block: Block) -> dict:
    return {
        "block_id": block.block_id,
        "number": block.number,
        "pages": [page_to_dict(page) for page in block.pages],
        "money_received": decimal_to_str(block.money_received),
        "whatsapp_phone": block.whatsapp_phone,
        "money_locked": block.money_locked,
    }


def result_to_dict(snapshot: ResultSnapshot | None) -> dict | None:
    if snapshot is None:
        return None
    return {
        "prizes": [
            {
                "prize_index": prize.prize_index,
                "milhar": prize.milhar,
                "group": prize.group,
            }
            for prize in snapshot.prizes
        ]
    }


def ui_state_to_dict(ui_state: UiState) -> dict:
    return {
        "geometry": ui_state.geometry,
        "window_state": ui_state.window_state,
        "splitter_state": ui_state.splitter_state,
        "selected_block_id": ui_state.selected_block_id,
        "selected_page_id": ui_state.selected_page_id,
        "selected_line_id": ui_state.selected_line_id,
        "selected_column": ui_state.selected_column,
        "extra": ui_state.extra,
    }


def app_state_to_dict(state: AppState) -> dict:
    return {
        "version": state.version,
        "blocks": [block_to_dict(block) for block in state.blocks],
        "result": result_to_dict(state.result),
        "percentage": str(state.percentage),
        "session_name": state.session_name,
        "total_paid_prizes": decimal_to_str(state.total_paid_prizes),
        "session_notes": state.session_notes,
        "whatsapp_map": state.whatsapp_map,
        "ui_state": ui_state_to_dict(state.ui_state),
    }


def dict_to_spec(payload: dict | None) -> BetSpec | None:
    if payload is None:
        return None
    return BetSpec(
        bet_type=BetType(payload["bet_type"]),
        numbers=list(payload["numbers"]),
        flags=[Flag(flag) for flag in payload.get("flags", [])],
        raw_text=payload.get("raw_text", ""),
        normalized_text=payload.get("normalized_text", ""),
        error_message=payload.get("error_message"),
    )


def dict_to_line(payload: dict) -> BetLine:
    return BetLine(
        line_id=payload["line_id"],
        raw_text=payload.get("raw_text", ""),
        spec=dict_to_spec(payload.get("spec")),
        value=Decimal(payload["value"]) if payload.get("value") is not None else None,
    )


def dict_to_page(payload: dict) -> Page:
    return Page(
        page_id=payload["page_id"],
        number=payload["number"],
        lines=[dict_to_line(item) for item in payload.get("lines", [])],
    )


def dict_to_block(payload: dict) -> Block:
    return Block(
        block_id=payload["block_id"],
        number=payload["number"],
        pages=[dict_to_page(item) for item in payload.get("pages", [])],
        money_received=Decimal(payload["money_received"]) if payload.get("money_received") else None,
        whatsapp_phone=payload.get("whatsapp_phone"),
        money_locked=payload.get("money_locked", False),
    )


def dict_to_result(payload: dict | None) -> ResultSnapshot | None:
    if payload is None:
        return None
    return ResultSnapshot(
        prizes=[
            ResultPrize(
                prize_index=item["prize_index"],
                milhar=item["milhar"],
                group=item["group"],
            )
            for item in payload.get("prizes", [])
        ]
    )


def dict_to_ui_state(payload: dict | None) -> UiState:
    if payload is None:
        return UiState()
    return UiState(
        geometry=payload.get("geometry"),
        window_state=payload.get("window_state"),
        splitter_state=payload.get("splitter_state"),
        selected_block_id=payload.get("selected_block_id"),
        selected_page_id=payload.get("selected_page_id"),
        selected_line_id=payload.get("selected_line_id"),
        selected_column=payload.get("selected_column", 0),
        extra=payload.get("extra", {}),
    )


def dict_to_app_state(payload: dict) -> AppState:
    return AppState(
        version=payload.get("version", 1),
        blocks=[dict_to_block(item) for item in payload.get("blocks", [])],
        result=dict_to_result(payload.get("result")),
        percentage=Decimal(payload.get("percentage", "0.70")),
        session_name=payload.get("session_name", ""),
        total_paid_prizes=Decimal(payload["total_paid_prizes"])
        if payload.get("total_paid_prizes") is not None
        else None,
        session_notes=payload.get("session_notes", ""),
        whatsapp_map=dict(payload.get("whatsapp_map", {})),
        ui_state=dict_to_ui_state(payload.get("ui_state")),
    )
