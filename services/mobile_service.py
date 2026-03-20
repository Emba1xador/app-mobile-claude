from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

from app_state.projections import build_ghost_value_hint
from core.entities import BetLine, Block, Page
from core.finance_engine import block_value_progress
from services.controller import BancaController
from services.formatting import format_money
from storage.active_session_store import ActiveSessionStore


class NoActiveSessionError(ValueError):
    pass


class MobileVisibilityError(ValueError):
    pass


class MobileSessionService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.active_session_store = ActiveSessionStore(root)
        self._write_lock = threading.Lock()

    def get_session_overview(self) -> dict:
        controller = self._require_controller()
        published_blocks, hidden_blocks_count = self._published_blocks(controller.state.blocks)
        blocks_payload = [self._block_payload(block) for block in published_blocks]
        filled_values, total_values = self._session_progress(published_blocks)
        page_count = sum(block["page_count"] for block in blocks_payload)
        pending_pages = sum(
            1
            for block in published_blocks
            for page in block.pages
            if self._status_from_progress(*self._page_progress(page)) == "pending"
        )
        draft_block_hidden = hidden_blocks_count > 0
        session_status = self._session_status(blocks_payload, draft_block_hidden)
        session_payload = {
            "mode": "pc_plus_mobile",
            "name": self._session_name(controller),
            "status": session_status,
            "updated_at": self._updated_at_text(),
            "has_blocks": bool(blocks_payload),
            "blocks_count": len(blocks_payload),
            "page_count": page_count,
            "pending_pages": pending_pages,
            "filled_values": filled_values,
            "total_values": total_values,
            "pending_blocks": sum(1 for block in blocks_payload if block["status"] == "pending"),
            "complete_blocks": sum(1 for block in blocks_payload if block["status"] == "complete"),
            "draft_block_hidden": draft_block_hidden,
            "hidden_blocks_count": hidden_blocks_count,
        }
        session_payload["session_revision"] = self._revision(
            {
                "session": {
                    "mode": session_payload["mode"],
                    "name": session_payload["name"],
                    "status": session_payload["status"],
                    "has_blocks": session_payload["has_blocks"],
                    "blocks_count": session_payload["blocks_count"],
                    "page_count": session_payload["page_count"],
                    "pending_pages": session_payload["pending_pages"],
                    "filled_values": session_payload["filled_values"],
                    "total_values": session_payload["total_values"],
                    "pending_blocks": session_payload["pending_blocks"],
                    "complete_blocks": session_payload["complete_blocks"],
                    "draft_block_hidden": session_payload["draft_block_hidden"],
                    "hidden_blocks_count": session_payload["hidden_blocks_count"],
                },
                "blocks": blocks_payload,
            }
        )
        return {
            "session": session_payload,
            "blocks": blocks_payload,
        }

    def list_pages(self, block_id: str) -> dict:
        controller = self._require_controller()
        block = self._find_visible_block(controller, block_id)
        return {
            "session_name": self._session_name(controller),
            "session_updated_at": self._updated_at_text(),
            "block": self._block_payload(block),
            "pages": [self._page_payload(block, page) for page in block.pages],
        }

    def get_page_detail(self, page_id: str) -> dict:
        controller = self._require_controller()
        block, page = self._find_visible_page(controller, page_id)
        return self._page_detail_payload(controller, block, page)

    def set_line_value(self, line_id: str, value_text: str) -> dict:
        with self._write_lock:
            controller = self._require_controller()
            block, page, _ = self._find_visible_line(controller, line_id)
            controller.set_line_value(line_id, value_text)
            payload = self._page_detail_payload(controller, block, page)
        payload["message"] = "Valor atualizado."
        return payload

    def fill_page(self, page_id: str, value_text: str) -> dict:
        with self._write_lock:
            controller = self._require_controller()
            block, page = self._find_visible_page(controller, page_id)
            controller.apply_value_to_pending_lines(page_id, value_text)
            payload = self._page_detail_payload(controller, block, page)
        payload["message"] = "Página preenchida."
        return payload

    def _page_detail_payload(self, controller: BancaController, block: Block, page: Page) -> dict:
        page_payload = self._page_payload(block, page)
        return {
            "session_name": self._session_name(controller),
            "session_updated_at": self._updated_at_text(),
            "block": {
                "block_id": block.block_id,
                "number": block.number,
                "block_revision": self._block_payload(block)["block_revision"],
            },
            "page": page_payload,
            "lines": self._page_lines_payload(block, page),
        }

    def _require_controller(self) -> BancaController:
        if not self.active_session_store.exists():
            raise NoActiveSessionError("Nenhuma sessão ativa encontrada. Abra ou crie uma sessão no desktop.")
        return BancaController(self.root)

    def _updated_at_text(self) -> str | None:
        updated_at = self.active_session_store.updated_at()
        if updated_at is None:
            return None
        return updated_at.isoformat(timespec="seconds")

    def _session_name(self, controller: BancaController) -> str:
        return controller.state.session_name.strip() or "Sessão ativa"

    def _published_blocks(self, blocks: list[Block]) -> tuple[list[Block], int]:
        if not blocks:
            return [], 0
        last_block = blocks[-1]
        if last_block.money_locked:
            return list(blocks), 0
        return list(blocks[:-1]), 1

    def _session_progress(self, blocks: list[Block]) -> tuple[int, int]:
        filled_total = 0
        value_total = 0
        for block in blocks:
            filled_values, total_values = block_value_progress(block)
            filled_total += filled_values
            value_total += total_values
        return filled_total, value_total

    def _session_status(self, blocks_payload: list[dict], draft_block_hidden: bool) -> str:
        if not blocks_payload:
            return "waiting_publish" if draft_block_hidden else "empty"
        if any(block["status"] == "pending" for block in blocks_payload):
            return "pending"
        if any(block["status"] == "complete" for block in blocks_payload):
            return "complete"
        return "empty"

    def _status_from_progress(self, filled_values: int, total_values: int) -> str:
        if total_values == 0:
            return "empty"
        if filled_values == total_values:
            return "complete"
        return "pending"

    def _block_payload(self, block: Block) -> dict:
        pages_payload = [self._page_payload(block, page) for page in block.pages]
        filled_values, total_values = block_value_progress(block)
        status = self._status_from_progress(filled_values, total_values)
        payload = {
            "block_id": block.block_id,
            "number": block.number,
            "page_count": len(block.pages),
            "filled_values": filled_values,
            "total_values": total_values,
            "pending_values": max(total_values - filled_values, 0),
            "pending_pages": sum(1 for page in pages_payload if page["status"] == "pending"),
            "complete_pages": sum(1 for page in pages_payload if page["status"] == "complete"),
            "status": status,
            "money_locked": block.money_locked,
            "next_pending_page_id": next(
                (page["page_id"] for page in pages_payload if page["status"] == "pending" and page["can_edit_values"]),
                None,
            ),
        }
        payload["block_revision"] = self._revision(
            {
                "block": {
                    "block_id": payload["block_id"],
                    "number": payload["number"],
                    "status": payload["status"],
                    "money_locked": payload["money_locked"],
                    "filled_values": payload["filled_values"],
                    "total_values": payload["total_values"],
                    "pending_pages": payload["pending_pages"],
                    "complete_pages": payload["complete_pages"],
                    "next_pending_page_id": payload["next_pending_page_id"],
                },
                "pages": pages_payload,
            }
        )
        return payload

    def _page_payload(self, block: Block, page: Page) -> dict:
        filled_values, total_values = self._page_progress(page)
        invalid_lines = sum(1 for line in page.lines if line.is_error)
        status = self._status_from_progress(filled_values, total_values)
        lock_payload = self._page_lock_payload(block)
        warning = lock_payload["lock_message"]
        if warning is None and total_values == 0:
            warning = "Página sem apostas válidas para lançamento."
        elif warning is None and invalid_lines:
            warning = "Página com apostas inválidas. Revise a estrutura no desktop."
        payload = {
            "page_id": page.page_id,
            "number": page.number,
            "bet_count": total_values,
            "filled_values": filled_values,
            "total_values": total_values,
            "pending_values": max(total_values - filled_values, 0),
            "status": status,
            "can_edit_values": bool(total_values) and not lock_payload["locked"],
            "warning": warning,
            "invalid_lines": invalid_lines,
            **lock_payload,
        }
        payload["page_revision"] = self._revision(
            {
                "page": {
                    "page_id": payload["page_id"],
                    "number": payload["number"],
                    "status": payload["status"],
                    "filled_values": payload["filled_values"],
                    "total_values": payload["total_values"],
                    "pending_values": payload["pending_values"],
                    "can_edit_values": payload["can_edit_values"],
                    "warning": payload["warning"],
                    "lock_kind": payload["lock_kind"],
                    "lock_reason": payload["lock_reason"],
                    "locked_by": payload["locked_by"],
                    "lock_message": payload["lock_message"],
                },
                "lines": self._page_lines_payload(block, page),
            }
        )
        return payload

    def _page_lock_payload(self, block: Block) -> dict[str, bool | str | None]:
        if block.money_locked:
            return {
                "locked": True,
                "lock_kind": "block_money",
                "lock_reason": "money_locked",
                "locked_by": "desktop",
                "lock_message": f"Bloco {block.number} bloqueado no financeiro.",
            }
        return {
            "locked": False,
            "lock_kind": None,
            "lock_reason": None,
            "locked_by": None,
            "lock_message": None,
        }

    def _page_lines_payload(self, block: Block, page: Page) -> list[dict]:
        rows: list[dict] = []
        for index, line in enumerate(page.lines, start=1):
            if line.is_empty:
                continue
            rows.append(self._line_payload(block, line, index))
        return rows

    def _line_payload(self, block: Block, line: BetLine, order: int) -> dict:
        if line.is_error:
            status = "invalid"
        elif line.is_valid_bet and line.value is not None:
            status = "filled"
        elif line.is_valid_bet:
            status = "pending"
        else:
            status = "readonly"
        return {
            "line_id": line.line_id,
            "order": order,
            "bet": line.spec.normalized_text if line.spec is not None else line.raw_text,
            "value": None if line.value is None else str(line.value),
            "value_display": "" if line.value is None else format_money(line.value),
            "placeholder": build_ghost_value_hint(line),
            "pending": line.is_valid_bet and line.value is None,
            "editable": line.is_valid_bet and not block.money_locked,
            "status": status,
            "error_message": line.spec.error_message if line.is_error and line.spec is not None else None,
        }

    def _page_progress(self, page: Page) -> tuple[int, int]:
        valid_lines = [line for line in page.lines if line.is_valid_bet]
        total = len(valid_lines)
        filled = sum(1 for line in valid_lines if line.value is not None)
        return filled, total

    def _find_visible_block(self, controller: BancaController, block_id: str) -> Block:
        published_blocks, _ = self._published_blocks(controller.state.blocks)
        for block in published_blocks:
            if block.block_id == block_id:
                return block
        if any(block.block_id == block_id for block in controller.state.blocks):
            raise MobileVisibilityError("Este bloco ainda está em digitação no desktop e não foi publicado para o mobile.")
        raise ValueError("Bloco não encontrado.")

    def _find_visible_page(self, controller: BancaController, page_id: str) -> tuple[Block, Page]:
        published_blocks, _ = self._published_blocks(controller.state.blocks)
        for block in published_blocks:
            for page in block.pages:
                if page.page_id == page_id:
                    return block, page
        for block in controller.state.blocks:
            for page in block.pages:
                if page.page_id == page_id:
                    raise MobileVisibilityError(
                        "Esta página ainda está em digitação no desktop e não foi publicada para o mobile."
                    )
        raise ValueError("Página não encontrada.")

    def _find_visible_line(self, controller: BancaController, line_id: str) -> tuple[Block, Page, BetLine]:
        published_blocks, _ = self._published_blocks(controller.state.blocks)
        for block in published_blocks:
            for page in block.pages:
                for line in page.lines:
                    if line.line_id == line_id:
                        return block, page, line
        for block in controller.state.blocks:
            for page in block.pages:
                for line in page.lines:
                    if line.line_id == line_id:
                        raise MobileVisibilityError(
                            "Esta linha ainda pertence a um bloco em digitação no desktop e não está visível no mobile."
                        )
        raise ValueError("Linha nao encontrada.")

    def _revision(self, payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:12]
