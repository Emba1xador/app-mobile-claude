from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
import logging
from pathlib import Path
import re
import threading

from app_state.projections import build_bets_projection, find_page
from app_state.session import AppState
from app_state.ui_state import UiState
from core.entities import BetLine, BetSpec, Block, Page, SummaryLine, make_id
from core.finance_engine import (
    block_total,
    block_value_progress,
    finance_row,
    quantize_money,
)
from core.enums import BetType, CommitMode
from core.page_lock import BlockLockedError, PageLockedError, is_page_locked
from core.parser import format_spec, parse_bet_input
from core.result_engine import build_result_snapshot, evaluate_line
from core.summary_engine import build_summary
from core.validators import ensure_numeric
from services.commands import SelectionContext
from services.formatting import format_money, parse_money
from storage.active_session_store import ActiveSessionStore, ActiveSessionToken
from storage.json_store import JsonStore
from storage.whatsapp_store import WhatsAppStore

FIXED_PERCENTAGE = Decimal("0.70")
LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ExternalValueSyncResult:
    line_ids: set[str] = field(default_factory=set)
    page_ids: set[str] = field(default_factory=set)
    block_ids: set[str] = field(default_factory=set)

    @property
    def has_changes(self) -> bool:
        return bool(self.line_ids or self.page_ids or self.block_ids)


class BancaController:
    def __init__(self, root: Path, *, restore_active_session: bool = True) -> None:
        self.root = root
        self.state = AppState()
        self.state_lock = threading.Lock()
        self.store = JsonStore(root)
        self.whatsapp_store = WhatsAppStore(root)
        self.active_session_store = ActiveSessionStore(root)
        self._active_session_token_seen: ActiveSessionToken | None = self.active_session_store.snapshot_token()
        self._active_session_tracking_enabled = False
        self._pending_external_values: dict[str, Decimal | None] = {}
        self._listeners: list[Callable[[], None]] = []
        whatsapp_map = self.whatsapp_store.load()
        self.state.whatsapp_map = whatsapp_map
        self.state.percentage = FIXED_PERCENTAGE
        active_state = self.active_session_store.try_load() if restore_active_session else None
        if active_state is not None:
            self._load_state_object(active_state, fallback_whatsapp_map=whatsapp_map)
            self._active_session_token_seen = self.active_session_store.snapshot_token()
            self._active_session_tracking_enabled = True

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def notify(
        self,
        *,
        protected_line_ids: set[str] | None = None,
        resolved_line_ids: set[str] | None = None,
    ) -> None:
        if self.has_meaningful_session():
            self._active_session_tracking_enabled = True
        self._sync_active_session(protected_line_ids=protected_line_ids, resolved_line_ids=resolved_line_ids)
        for listener in list(self._listeners):
            listener()

    def ensure_bootstrap(self) -> None:
        self._recompute()
        self.notify()

    def has_meaningful_session(self, state: AppState | None = None) -> bool:
        target_state = state or self.state
        return self._state_has_meaningful_content(target_state)

    def has_active_runtime_session(self) -> bool:
        return self.active_session_store.exists()

    def has_resumable_active_session(self) -> bool:
        active_state = self.active_session_store.try_load()
        return active_state is not None and self._state_has_meaningful_content(active_state)

    def restore_active_session(self) -> bool:
        active_state = self.active_session_store.try_load()
        if active_state is None or not self._state_has_meaningful_content(active_state):
            return False
        fallback_whatsapp_map = self.whatsapp_store.load()
        self._load_state_object(active_state, fallback_whatsapp_map=fallback_whatsapp_map)
        self._active_session_token_seen = self.active_session_store.snapshot_token()
        self._active_session_tracking_enabled = True
        self.notify()
        return True

    def discard_active_runtime_session(self) -> None:
        self.active_session_store.clear()
        self._active_session_token_seen = None
        self._pending_external_values.clear()
        self._active_session_tracking_enabled = self.has_meaningful_session()

    def start_new_session(self, ui_state: UiState | None = None) -> None:
        whatsapp_map = dict(self.whatsapp_store.load() or self.state.whatsapp_map)
        self.active_session_store.clear()
        self._active_session_token_seen = None
        self._active_session_tracking_enabled = False
        self._load_state_object(
            AppState(
                percentage=FIXED_PERCENTAGE,
                whatsapp_map=whatsapp_map,
                ui_state=ui_state or UiState(),
            ),
            fallback_whatsapp_map=whatsapp_map,
        )
        self.notify()

    def end_session(
        self,
        *,
        protected_line_ids: set[str] | None = None,
        ui_state: UiState | None = None,
    ) -> Path | None:
        save_path = None
        if self.has_meaningful_session():
            save_path = self.save_session(path=None, protected_line_ids=protected_line_ids)
        self.start_new_session(ui_state=ui_state)
        return save_path

    def create_block(self, number: str) -> tuple[str, str, str]:
        normalized_number = number.strip()
        if not normalized_number or not normalized_number.isdigit():
            raise ValueError("N\u00famero do bloco inv\u00e1lido.")
        block = Block(block_id=make_id(), number=normalized_number.zfill(3))
        block.whatsapp_phone = self.state.whatsapp_map.get(block.number)
        page = self._new_page(1)
        block.pages.append(page)
        self.state.blocks.append(block)
        self._recompute()
        self.notify()
        return block.block_id, page.page_id, page.lines[0].line_id

    def create_page_after(self, page_id: str, force_unlock: bool = False) -> tuple[str, str]:
        block, page = self._get_page(page_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_page_mutation(block, page, force_unlock)
        index = block.pages.index(page) + 1
        new_page = self._new_page(page.number + 1)
        block.pages.insert(index, new_page)
        self._renumber_pages(block)
        self._recompute()
        self.notify()
        return new_page.page_id, new_page.lines[0].line_id

    def upsert_bet_text(
        self,
        line_id: str,
        text: str,
        commit_mode,
        force_unlock: bool = False,
    ) -> str:
        block, page, line = self._get_line(line_id)
        changed = text.strip() != (line.raw_text or "").strip()
        if changed:
            self._guard_block_mutation(block, force_unlock)
            self._guard_page_mutation(block, page, force_unlock)
        parsed = parse_bet_input(text, commit_mode=commit_mode)
        parsed = self._normalize_committed_spec(parsed, commit_mode)
        line.raw_text = text.strip()
        line.spec = parsed
        if parsed is not None and parsed.is_valid:
            self._canonicalize_valid_line(line)
        elif parsed is None:
            line.spec = None
        self._ensure_trailing_blank_line(page)
        self._recompute()
        self.notify(resolved_line_ids={line_id})
        return line.line_id

    def toggle_mc(self, line_ids: list[str], force_unlock: bool = False) -> None:
        pages_touched: set[str] = set()
        lines = [self._get_line(line_id) for line_id in line_ids]
        for block, page, line in lines:
            pages_touched.add(page.page_id)
            if line.spec is None or line.spec.bet_type.value != "M":
                continue
            self._guard_block_mutation(block, force_unlock)
            self._guard_page_mutation(block, page, force_unlock)
            next_spec = parse_bet_input(
                self._build_spec_text(BetType.MILHAR_CENTENA, line.spec.numbers, line.spec.flags)
            )
            if next_spec is None or not next_spec.is_valid:
                continue
            line.spec = next_spec
            line.raw_text = next_spec.normalized_text
        if pages_touched:
            self._recompute()
            self.notify(resolved_line_ids=set(line_ids))

    def apply_flag(self, line_ids: list[str], flag, mode: str = "toggle", force_unlock: bool = False) -> bool:
        changed = False
        lines = [self._get_line(line_id) for line_id in line_ids]
        for block, page, line in lines:
            if line.spec is None or not line.spec.is_valid:
                continue
            next_spec = self._build_flagged_spec(line, flag, mode)
            if next_spec is None:
                continue
            self._guard_block_mutation(block, force_unlock)
            self._guard_page_mutation(block, page, force_unlock)
            line.spec = next_spec
            line.raw_text = next_spec.normalized_text
            changed = True
        if changed:
            self._recompute()
            self.notify(resolved_line_ids=set(line_ids))
        return changed

    def clear_flags(self, line_ids: list[str], force_unlock: bool = False) -> None:
        changed = False
        lines = [self._get_line(line_id) for line_id in line_ids]
        for block, page, line in lines:
            if line.spec is None or not line.spec.is_valid or not line.spec.flags:
                continue
            next_spec = parse_bet_input(self._build_spec_text(line.spec.bet_type, line.spec.numbers))
            if next_spec is None or not next_spec.is_valid:
                continue
            self._guard_block_mutation(block, force_unlock)
            self._guard_page_mutation(block, page, force_unlock)
            line.spec = next_spec
            line.raw_text = next_spec.normalized_text
            changed = True
        if changed:
            self._recompute()
            self.notify(resolved_line_ids=set(line_ids))

    def transform_lines(self, line_ids: list[str], target_type: BetType, force_unlock: bool = False) -> None:
        changed = False
        lines = [self._get_line(line_id) for line_id in line_ids]
        for block, page, line in lines:
            next_spec = self._build_transformed_spec(line, target_type)
            if next_spec is None:
                continue
            if self._line_matches_spec(line, next_spec):
                continue
            self._guard_block_mutation(block, force_unlock)
            self._guard_page_mutation(block, page, force_unlock)
            line.spec = next_spec
            line.raw_text = next_spec.normalized_text
            changed = True
        if changed:
            self._recompute()
            self.notify(resolved_line_ids=set(line_ids))

    def set_line_value(self, line_id: str, text: str, force_unlock: bool = False) -> None:
        block, page, line = self._get_line(line_id)
        value = parse_money(text)
        if block.money_locked and line.value != value:
            self._guard_block_mutation(block, force_unlock)
        if line.is_empty and value is not None:
            raise ValueError("Preencha a aposta antes do valor.")
        if value is not None and not line.is_valid_bet:
            raise ValueError("Somente apostas v\u00e1lidas podem receber valor.")
        line.value = value
        self._ensure_trailing_blank_line(page)
        self._recompute()
        self.notify(resolved_line_ids={line_id})

    def apply_value_to_page(self, page_id: str, value_text: str, force_unlock: bool = False) -> None:
        block, page = self._get_page(page_id)
        value = parse_money(value_text)
        if block.money_locked:
            changed = any(line.is_valid_bet and line.value != value for line in page.lines)
            if changed:
                self._guard_block_mutation(block, force_unlock)
        resolved_line_ids: set[str] = set()
        for line in page.lines:
            if line.is_valid_bet:
                line.value = value
                resolved_line_ids.add(line.line_id)
        self._recompute()
        self.notify(resolved_line_ids=resolved_line_ids)

    def apply_value_to_pending_lines(self, page_id: str, value_text: str, force_unlock: bool = False) -> None:
        block, page = self._get_page(page_id)
        value = parse_money(value_text)
        pending_lines = [line for line in page.lines if line.is_valid_bet and line.value is None]
        if not pending_lines:
            return
        if block.money_locked:
            changed = any(line.value != value for line in pending_lines)
            if changed:
                self._guard_block_mutation(block, force_unlock)
        for line in pending_lines:
            line.value = value
        self._recompute()
        self.notify(resolved_line_ids={line.line_id for line in pending_lines})

    def set_result(self, numbers: list[str]) -> None:
        if len(numbers) != 5 or any(not number.isdigit() or len(number) != 4 for number in numbers):
            raise ValueError("O resultado precisa conter 5 milhares.")
        self.state.result = build_result_snapshot(numbers)
        self._recompute()
        self.notify()

    def set_percentage(self, value_text: str) -> None:
        del value_text
        self.state.percentage = FIXED_PERCENTAGE
        self._recompute()
        self.notify()

    def set_block_money(self, block_id: str, value_text: str, force_unlock: bool = False) -> None:
        block = self._get_block(block_id)
        new_value = parse_money(value_text)
        if block.money_locked and block.money_received != new_value:
            self._guard_block_mutation(block, force_unlock)
        block.money_received = new_value
        block.money_locked = new_value is not None
        self._recompute()
        self.notify()

    def set_block_whatsapp(self, block_id: str, phone: str) -> None:
        block = self._get_block(block_id)
        block.whatsapp_phone = phone or None
        if block.whatsapp_phone:
            self.state.whatsapp_map[block.number] = block.whatsapp_phone
        elif block.number in self.state.whatsapp_map:
            self.state.whatsapp_map.pop(block.number)
        self.whatsapp_store.save(self.state.whatsapp_map)
        self.notify()

    def insert_line_above(self, line_id: str, force_unlock: bool = False) -> str:
        block, page, line = self._get_line(line_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_page_mutation(block, page, force_unlock)
        index = page.lines.index(line)
        new_line = self._new_line()
        page.lines.insert(index, new_line)
        self._ensure_trailing_blank_line(page)
        self._recompute()
        self.notify()
        return new_line.line_id

    def insert_line_below(self, line_id: str, force_unlock: bool = False) -> str:
        block, page, line = self._get_line(line_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_page_mutation(block, page, force_unlock)
        index = page.lines.index(line) + 1
        new_line = self._new_line()
        page.lines.insert(index, new_line)
        self._ensure_trailing_blank_line(page)
        self._recompute()
        self.notify()
        return new_line.line_id

    def delete_line(self, line_id: str, force_unlock: bool = False) -> str | None:
        block, page, line = self._get_line(line_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_page_mutation(block, page, force_unlock)
        index = page.lines.index(line)
        page.lines.pop(index)
        if not page.lines:
            page.lines.append(self._new_line())
        self._ensure_trailing_blank_line(page)
        self._recompute()
        self.notify(resolved_line_ids={line_id})
        if index < len(page.lines):
            return page.lines[index].line_id
        return page.lines[-1].line_id

    def delete_page(self, page_id: str, force_unlock: bool = False) -> str | None:
        block, page = self._get_page(page_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_page_mutation(block, page, force_unlock)
        index = block.pages.index(page)
        resolved_line_ids = {line.line_id for line in page.lines}
        block.pages.pop(index)
        if not block.pages:
            self.state.blocks.remove(block)
            self._recompute()
            self.notify(resolved_line_ids=resolved_line_ids)
            return None
        self._renumber_pages(block)
        self._recompute()
        self.notify(resolved_line_ids=resolved_line_ids)
        return block.pages[min(index, len(block.pages) - 1)].page_id

    def delete_block(self, block_id: str, force_unlock: bool = False) -> None:
        block = self._get_block(block_id)
        self._guard_block_mutation(block, force_unlock)
        self._guard_block_pages_mutation(block, force_unlock)
        resolved_line_ids = {line.line_id for page in block.pages for line in page.lines}
        self.state.blocks.remove(block)
        if self.state.ui_state.selected_block_id == block_id:
            self.state.ui_state.selected_block_id = None
            self.state.ui_state.selected_page_id = None
            self.state.ui_state.selected_line_id = None
        self._recompute()
        self.notify(resolved_line_ids=resolved_line_ids)

    def clear_page_values(self, page_id: str) -> None:
        _, page = self._get_page(page_id)
        resolved_line_ids = {line.line_id for line in page.lines}
        for line in page.lines:
            line.value = None
        self._recompute()
        self.notify(resolved_line_ids=resolved_line_ids)

    def save_session(
        self,
        path: Path | None = None,
        *,
        protected_line_ids: set[str] | None = None,
    ) -> Path:
        self.whatsapp_store.save(self.state.whatsapp_map)
        state_to_save = self._prepare_state_for_persistence(protected_line_ids=protected_line_ids)
        if self._state_has_meaningful_content(state_to_save):
            self._active_session_tracking_enabled = True
            self._save_active_session_snapshot(state_to_save)
        else:
            self.active_session_store.clear()
            self._active_session_token_seen = None
            self._active_session_tracking_enabled = False
        return self.store.save(state_to_save, path=path)

    def load_session(self, path: Path) -> None:
        self._load_state_object(self.store.load(path), fallback_whatsapp_map=self.whatsapp_store.load())
        self._active_session_tracking_enabled = self.has_meaningful_session()
        if not self._active_session_tracking_enabled:
            self.active_session_store.clear()
            self._active_session_token_seen = None
        self.notify()

    def set_ui_state(self, ui_state: UiState) -> None:
        self.state.ui_state = ui_state

    def update_selection(self, selection: SelectionContext) -> None:
        self.state.ui_state.selected_block_id = selection.block_id
        self.state.ui_state.selected_page_id = selection.page_id
        self.state.ui_state.selected_line_id = selection.line_id
        self.state.ui_state.selected_column = selection.column

    def focus_block(self, block_id: str) -> tuple[str | None, str | None]:
        block = self._get_block(block_id)
        self.state.ui_state.selected_block_id = block.block_id
        if not block.pages:
            self.state.ui_state.selected_page_id = None
            self.state.ui_state.selected_line_id = None
            return None, None
        page = block.pages[0]
        self.state.ui_state.selected_page_id = page.page_id
        line = next((item for item in page.lines if True), None)
        self.state.ui_state.selected_line_id = line.line_id if line else None
        self.notify()
        return page.page_id, self.state.ui_state.selected_line_id

    def unlock_block(self, block_id: str) -> None:
        block = self._get_block(block_id)
        block.money_locked = False
        self.notify()

    def set_total_paid_prizes(
        self,
        value_text: str,
        *,
        protected_line_ids: set[str] | None = None,
    ) -> None:
        self.state.total_paid_prizes = parse_money(value_text)
        self.notify(protected_line_ids=protected_line_ids)

    def set_session_notes(
        self,
        text: str,
        *,
        protected_line_ids: set[str] | None = None,
    ) -> None:
        self.state.session_notes = text
        self.notify(protected_line_ids=protected_line_ids)

    def set_session_name(
        self,
        text: str,
        *,
        protected_line_ids: set[str] | None = None,
    ) -> None:
        self.state.session_name = text.strip()
        self.notify(protected_line_ids=protected_line_ids)

    def sync_external_mobile_values_if_needed(
        self,
        protected_line_ids: set[str] | None = None,
    ) -> ExternalValueSyncResult:
        return self._merge_external_mobile_values(protected_line_ids=protected_line_ids)

    def get_projection(self):
        return build_bets_projection(self.state.blocks)

    def get_finance_rows(self):
        rows = []
        for block in self.state.blocks:
            has_winner = any(line.winners for page in block.pages for line in page.lines)
            rows.append(finance_row(block, self.state.percentage, has_winner=has_winner))
        return rows

    def get_summary(self) -> list[SummaryLine]:
        return build_summary(self.state.blocks, self.state.result is not None)

    def get_bottom_bar_data(self) -> dict[str, str]:
        block_id = self.state.ui_state.selected_block_id or (self.state.blocks[0].block_id if self.state.blocks else None)
        page_id = self.state.ui_state.selected_page_id
        block = self._get_block(block_id) if block_id else None
        page_data = find_page(self.state.blocks, page_id) if page_id else None
        current_page = page_data[1] if page_data else None
        bruto = block_total(block) if block else Decimal("0")
        liquido = quantize_money(bruto * self.state.percentage) if block else Decimal("0")
        filled_values, total_values = block_value_progress(block) if block else (0, 0)
        progress_text = f"{filled_values}/{total_values}"
        return {
            "block": block.number if block else "---",
            "selected_block_id": block.block_id if block else "",
            "bruto": str(bruto),
            "liquido": str(liquido),
            "dinheiro": str(block.money_received) if block and block.money_received is not None else "",
            "resultado": str(quantize_money(block.money_received - liquido))
            if block and block.money_received is not None
            else "",
            "progress_text": progress_text,
            "filled_values": str(filled_values),
            "total_values": str(total_values),
            "blocks": [{"block_id": item.block_id, "number": item.number} for item in self.state.blocks],
            "current_page": str(current_page.number) if current_page is not None else "",
        }

    def get_finance_totals_data(self) -> dict[str, str | int]:
        finance_rows = self.get_finance_rows()
        total_received = quantize_money(
            sum((block.money_received or Decimal("0") for block in self.state.blocks), Decimal("0"))
        )
        total_bruto = quantize_money(sum((row.bruto for row in finance_rows), Decimal("0")))
        total_liquido = quantize_money(sum((row.liquido for row in finance_rows), Decimal("0")))
        total_paid_prizes = self.state.total_paid_prizes or Decimal("0")
        cash_balance = quantize_money(total_received - total_paid_prizes)
        return {
            "total_received": str(total_received),
            "total_bruto": str(total_bruto),
            "total_liquido": str(total_liquido),
            "total_paid_prizes": str(self.state.total_paid_prizes) if self.state.total_paid_prizes is not None else "",
            "cash_balance": str(cash_balance),
            "blocks_processed": len(self.state.blocks),
            "session_notes": self.state.session_notes,
        }

    def get_session_overview_data(self) -> dict[str, object]:
        blocks: list[dict[str, object]] = []
        awarded_blocks: list[dict[str, object]] = []

        for block in self.state.blocks:
            page_count = len(block.pages)
            bet_count = sum(1 for page in block.pages for line in page.lines if line.is_valid_bet)
            prize_count = sum(len(line.winners) for page in block.pages for line in page.lines)
            pending_count = 0
            for page in block.pages:
                valid_lines = [line for line in page.lines if line.is_valid_bet]
                if valid_lines and any(line.value is None for line in valid_lines):
                    pending_count += 1
                if any(line.is_error for line in page.lines):
                    pending_count += 1
            if block.money_received is None:
                pending_count += 1
            if not block.whatsapp_phone:
                pending_count += 1

            if block.block_id == self.state.ui_state.selected_block_id:
                state_label = "em edição"
            elif prize_count > 0:
                state_label = "1 prêmio" if prize_count == 1 else f"{prize_count} prêmios"
            elif pending_count > 0:
                state_label = "pendente" if pending_count == 1 else f"{pending_count} pendências"
            else:
                state_label = "ok"

            blocks.append(
                {
                    "block_id": block.block_id,
                    "block_number": block.number,
                    "page_count": page_count,
                    "bet_count": bet_count,
                    "prize_count": prize_count,
                    "pending_count": pending_count,
                    "state_label": state_label,
                    "is_current": block.block_id == self.state.ui_state.selected_block_id,
                }
            )

            details: list[dict[str, object]] = []
            for page in block.pages:
                valid_lines = [line for line in page.lines if line.is_valid_bet]
                for position, line in enumerate(valid_lines, start=1):
                    if not line.winners or line.spec is None:
                        continue
                    for winner in line.winners:
                        prize_text = f"{winner.prize_label} prêmio" if winner.prize_label != "GERAL" else winner.detail
                        details.append(
                            {
                                "text": (
                                    f"{line.spec.normalized_text} • Pág. {page.number} • "
                                    f"Linha {position} • {prize_text}"
                                ),
                                "bet_text": line.spec.normalized_text,
                                "line_number": position,
                                "page_number": page.number,
                                "prize_label": winner.prize_label,
                                "winner_detail": winner.detail,
                                "prize_index": winner.prize_index,
                            }
                        )

            if details:
                details.sort(
                    key=lambda item: (
                        int(item["prize_index"]),
                        int(item["page_number"]),
                        int(item["line_number"]),
                    )
                )
                awarded_blocks.append(
                    {
                        "block_id": block.block_id,
                        "block_number": block.number,
                        "page_count": page_count,
                        "prize_count": len(details),
                        "details": details,
                    }
                )

        awarded_blocks.sort(key=lambda item: (-int(item["prize_count"]), str(item["block_number"])))

        return {
            "result_loaded": self.state.result is not None,
            "selected_block_id": self.state.ui_state.selected_block_id or "",
            "blocks": blocks,
            "awarded_blocks": awarded_blocks,
        }

    def get_operational_pendencies(self) -> dict[str, object]:
        groups: list[dict[str, object]] = []

        if self.state.result is None:
            groups.append(
                {
                    "group_id": "session",
                    "title": "Sessão",
                    "critical_count": 1,
                    "warning_count": 0,
                    "total_count": 1,
                    "tone": "critical",
                    "items": ["Resultado não informado"],
                }
            )

        for block in self.state.blocks:
            critical_items: list[str] = []
            warning_items: list[str] = []
            critical_count = 0
            warning_count = 0
            pending_pages: list[int] = []
            invalid_pages: list[int] = []

            if block.money_received is None:
                critical_items.append("Dinheiro não informado")
                critical_count += 1
            if not block.whatsapp_phone:
                critical_items.append("Contato não configurado")
                critical_count += 1

            for page in block.pages:
                valid_lines = [line for line in page.lines if line.is_valid_bet]
                if valid_lines and any(line.value is None for line in valid_lines):
                    pending_pages.append(page.number)
                if any(line.is_error for line in page.lines):
                    invalid_pages.append(page.number)

            if pending_pages:
                critical_items.append(self._page_issue_label(pending_pages, "pendente", "pendentes"))
                critical_count += len(pending_pages)
            if invalid_pages:
                warning_items.append(self._page_issue_label(invalid_pages, "com aposta inválida", "com aposta inválida"))
                warning_count += len(invalid_pages)

            all_items = critical_items + warning_items
            total_count = critical_count + warning_count
            if all_items:
                groups.append(
                    {
                        "group_id": f"block:{block.block_id}",
                        "title": f"Bloco {block.number}",
                        "critical_count": critical_count,
                        "warning_count": warning_count,
                        "total_count": total_count,
                        "tone": "critical" if critical_count > 0 else "warning",
                        "items": all_items,
                    }
                )

        return {
            "groups": groups,
            "ready_message": "Horário pronto para fechamento.",
        }

    def _page_issue_label(self, page_numbers: list[int], singular_suffix: str, plural_suffix: str) -> str:
        prefix = "P\u00e1gina" if len(page_numbers) == 1 else "P\u00e1ginas"
        suffix = singular_suffix if len(page_numbers) == 1 else plural_suffix
        return f"{prefix} {self._compress_page_numbers(page_numbers)} {suffix}"

    def _compress_page_numbers(self, page_numbers: list[int]) -> str:
        if not page_numbers:
            return ""
        ordered = sorted(set(page_numbers))
        ranges: list[str] = []
        start = ordered[0]
        end = start
        for number in ordered[1:]:
            if number == end + 1:
                end = number
                continue
            ranges.append(str(start) if start == end else f"{start}-{end}")
            start = end = number
        ranges.append(str(start) if start == end else f"{start}-{end}")
        return ", ".join(ranges)

    def build_whatsapp_message(self, block_id: str) -> str:
        row = next(item for item in self.get_finance_rows() if item.block_id == block_id)
        lines = [
            f"Bloco {row.block_number}",
            f"Bruto: {format_money(row.bruto)}",
            f"Líquido (70%): {format_money(row.liquido)}",
            f"Dinheiro recebido: {format_money(row.money_received)}",
            f"Saldo: {format_money(row.resultado)}",
        ]
        return "\n".join(lines)

    def resolve_flag_input(
        self,
        text: str,
        flag,
        mode: str = "toggle",
        commit_mode: CommitMode = CommitMode.ENTER,
    ) -> str | None:
        spec = parse_bet_input(text, commit_mode=commit_mode)
        if spec is None or not spec.is_valid:
            return None
        flags = list(spec.flags)
        if mode == "toggle":
            if flag in flags:
                flags.remove(flag)
            else:
                flags.append(flag)
        elif mode == "add":
            if flag not in flags:
                flags.append(flag)
        else:
            raise ValueError("Modo de flag inv\u00e1lido.")
        candidate_text = self._build_spec_text(spec.bet_type, spec.numbers, flags)
        candidate = parse_bet_input(candidate_text, commit_mode=commit_mode)
        if candidate is None or not candidate.is_valid:
            return None
        return format_spec(candidate)

    def _build_flagged_spec(self, line: BetLine, flag, mode: str) -> BetSpec | None:
        if line.spec is None or not line.spec.is_valid:
            return None
        flags = list(line.spec.flags)
        if mode == "toggle":
            if flag in flags:
                flags.remove(flag)
            else:
                flags.append(flag)
        elif mode == "add":
            if flag in flags:
                return None
            flags.append(flag)
        else:
            raise ValueError("Modo de flag inv\u00e1lido.")
        text = self._build_spec_text(line.spec.bet_type, line.spec.numbers, flags)
        spec = parse_bet_input(text)
        if spec is None or not spec.is_valid:
            return None
        return spec

    def _build_transformed_spec(self, line: BetLine, target_type: BetType) -> BetSpec | None:
        source_numbers = self._extract_transform_numbers(line)
        if not source_numbers:
            return None
        target_numbers = self._numbers_for_target(source_numbers, target_type)
        if target_numbers is None:
            return None
        base_text = self._build_spec_text(target_type, target_numbers)
        base_spec = parse_bet_input(base_text)
        if base_spec is None or not base_spec.is_valid or base_spec.bet_type != target_type:
            return None
        preserved_flags: list = []
        if line.spec is not None and line.spec.is_valid:
            for flag in line.spec.flags:
                candidate_text = self._build_spec_text(target_type, base_spec.numbers, preserved_flags + [flag])
                candidate_spec = parse_bet_input(candidate_text)
                if candidate_spec is not None and candidate_spec.is_valid and candidate_spec.bet_type == target_type:
                    preserved_flags.append(flag)
        final_text = self._build_spec_text(target_type, base_spec.numbers, preserved_flags)
        final_spec = parse_bet_input(final_text)
        if final_spec is None or not final_spec.is_valid or final_spec.bet_type != target_type:
            return None
        return final_spec

    def _extract_transform_numbers(self, line: BetLine) -> list[str]:
        if line.spec is not None and line.spec.is_valid:
            return list(line.spec.numbers)
        return re.findall(r"\d+", line.raw_text)

    def _numbers_for_target(self, numbers: list[str], target_type: BetType) -> list[str] | None:
        if target_type == BetType.CENTENA:
            return [numbers[0]] if len(numbers) == 1 and ensure_numeric(numbers[0], 3) else None
        if target_type in {BetType.MILHAR, BetType.MILHAR_CENTENA}:
            return [numbers[0]] if len(numbers) == 1 and ensure_numeric(numbers[0], 4) else None
        if target_type == BetType.DEZENA:
            return [numbers[0]] if len(numbers) == 1 and ensure_numeric(numbers[0], 2) else None
        if target_type == BetType.DUQUE_DEZENA:
            return list(numbers) if len(numbers) == 2 and all(ensure_numeric(number, 2) for number in numbers) else None
        if target_type == BetType.TERNO_DEZENA:
            return list(numbers) if len(numbers) == 3 and all(ensure_numeric(number, 2) for number in numbers) else None
        if target_type == BetType.GRUPO:
            if len(numbers) != 1 or not numbers[0].isdigit():
                return None
            return [numbers[0]] if 1 <= int(numbers[0]) <= 25 else None
        if target_type == BetType.TERNO_GRUPO:
            if len(numbers) != 3 or any(not number.isdigit() or not 1 <= int(number) <= 25 for number in numbers):
                return None
            return list(numbers)
        if target_type == BetType.FECHAMENTO:
            if len(numbers) != 2 or any(not ensure_numeric(number, 3) for number in numbers):
                return None
            return list(numbers) if int(numbers[0]) <= int(numbers[1]) else None
        return None

    def _build_spec_text(self, bet_type: BetType, numbers: list[str], flags: list | None = None) -> str:
        base = (
            f"F {numbers[0]} / {numbers[1]}"
            if bet_type == BetType.FECHAMENTO and len(numbers) == 2
            else f"{bet_type.value} {' '.join(numbers)}"
        )
        if flags:
            base = f"{base} {' '.join(flag.value for flag in flags)}"
        return base.strip()

    def _line_matches_spec(self, line: BetLine, spec: BetSpec) -> bool:
        if line.spec is None:
            return False
        return (
            line.spec.bet_type == spec.bet_type
            and line.spec.numbers == spec.numbers
            and line.spec.flags == spec.flags
        )

    def _normalize_committed_spec(self, spec: BetSpec | None, commit_mode) -> BetSpec | None:
        if (
            spec is None
            or not spec.is_valid
            or commit_mode != CommitMode.SHIFT_MC
            or spec.bet_type != BetType.MILHAR
            or len(spec.numbers) != 1
            or not ensure_numeric(spec.numbers[0], 4)
        ):
            return spec
        promoted = parse_bet_input(self._build_spec_text(BetType.MILHAR_CENTENA, spec.numbers, spec.flags))
        if promoted is None or not promoted.is_valid:
            return spec
        return promoted

    def _canonicalize_valid_line(self, line: BetLine) -> None:
        if line.spec is None or not line.spec.is_valid:
            return
        line.spec.normalized_text = format_spec(line.spec)
        line.raw_text = line.spec.normalized_text

    def _canonicalize_loaded_line(self, line: BetLine) -> None:
        if line.spec is None:
            return
        if line.spec.is_valid:
            refreshed = parse_bet_input(format_spec(line.spec))
            if refreshed is not None and refreshed.is_valid:
                line.spec = refreshed
            self._canonicalize_valid_line(line)
            return
        line.spec.normalized_text = "ERRO"

    def _load_state_object(self, state: AppState, fallback_whatsapp_map: dict[str, str] | None = None) -> None:
        self.state = state
        self._pending_external_values.clear()
        merged_whatsapp_map = dict(fallback_whatsapp_map or {})
        merged_whatsapp_map.update(self.state.whatsapp_map or {})
        self.state.whatsapp_map = merged_whatsapp_map
        self.state.percentage = FIXED_PERCENTAGE
        self.state.session_name = self.state.session_name.strip()
        self.state.session_notes = self.state.session_notes or ""
        for block in self.state.blocks:
            for page in block.pages:
                for line in page.lines:
                    self._canonicalize_loaded_line(line)
        for block in self.state.blocks:
            if block.whatsapp_phone:
                self.state.whatsapp_map[block.number] = block.whatsapp_phone
            elif block.number in self.state.whatsapp_map:
                block.whatsapp_phone = self.state.whatsapp_map[block.number]
        self._recompute()
        self.whatsapp_store.save(self.state.whatsapp_map)

    def _sync_active_session(
        self,
        *,
        protected_line_ids: set[str] | None = None,
        resolved_line_ids: set[str] | None = None,
    ) -> None:
        if not self._should_persist_active_session():
            if self._active_session_tracking_enabled:
                self.active_session_store.clear()
                self._active_session_token_seen = None
                self._active_session_tracking_enabled = False
            return
        try:
            state_to_persist = self._prepare_state_for_persistence(
                protected_line_ids=protected_line_ids,
                resolved_line_ids=resolved_line_ids,
            )
            self._save_active_session_snapshot(state_to_persist)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Falha ao sincronizar sessao ativa: %s", exc)

    def _should_persist_active_session(self) -> bool:
        return self._active_session_tracking_enabled and self.has_meaningful_session()

    def _state_has_meaningful_content(self, state: AppState) -> bool:
        return bool(
            state.blocks
            or state.result is not None
            or state.session_name.strip()
            or state.total_paid_prizes is not None
            or state.session_notes.strip()
        )

    def _recompute(self) -> None:
        self.state.percentage = FIXED_PERCENTAGE
        for block in self.state.blocks:
            for page in block.pages:
                self._ensure_trailing_blank_line(page)
                for line in page.lines:
                    line.winners = evaluate_line(line, self.state.result)

    def _get_block(self, block_id: str | None) -> Block:
        if block_id is None:
            raise ValueError("Bloco n\u00e3o selecionado.")
        for block in self.state.blocks:
            if block.block_id == block_id:
                return block
        raise ValueError("Bloco n\u00e3o encontrado.")

    def _get_page(self, page_id: str) -> tuple[Block, Page]:
        for block in self.state.blocks:
            for page in block.pages:
                if page.page_id == page_id:
                    return block, page
        raise ValueError("P\u00e1gina n\u00e3o encontrada.")

    def _get_line(self, line_id: str) -> tuple[Block, Page, BetLine]:
        for block in self.state.blocks:
            for page in block.pages:
                for line in page.lines:
                    if line.line_id == line_id:
                        return block, page, line
        raise ValueError("Linha n\u00e3o encontrada.")

    def _new_page(self, number: int) -> Page:
        return Page(page_id=make_id(), number=number, lines=[self._new_line()])

    def _new_line(self) -> BetLine:
        return BetLine(line_id=make_id())

    def _line_lookup(self, blocks: list[Block]) -> dict[str, tuple[str, str, BetLine]]:
        lookup: dict[str, tuple[str, str, BetLine]] = {}
        for block in blocks:
            for page in block.pages:
                for line in page.lines:
                    lookup[line.line_id] = (block.block_id, page.page_id, line)
        return lookup

    def _line_value_lookup(self, blocks: list[Block]) -> dict[str, Decimal | None]:
        values: dict[str, Decimal | None] = {}
        for block in blocks:
            for page in block.pages:
                for line in page.lines:
                    values[line.line_id] = line.value
        return values

    def _prepare_state_for_persistence(
        self,
        *,
        protected_line_ids: set[str] | None = None,
        resolved_line_ids: set[str] | None = None,
    ) -> AppState:
        with self.state_lock:
            self._merge_external_mobile_values(
                protected_line_ids=protected_line_ids,
                resolved_line_ids=resolved_line_ids,
            )
            state_to_persist = deepcopy(self.state)
            if self._pending_external_values:
                self._overlay_line_values_on_state(state_to_persist, self._pending_external_values)
        return state_to_persist

    def _save_active_session_snapshot(self, state: AppState) -> None:
        self.active_session_store.save(state)
        self._active_session_token_seen = self.active_session_store.snapshot_token()

    def _merge_external_mobile_values(
        self,
        *,
        protected_line_ids: set[str] | None = None,
        resolved_line_ids: set[str] | None = None,
    ) -> ExternalValueSyncResult:
        protected_line_ids = set(protected_line_ids or ())
        resolved_line_ids = set(resolved_line_ids or ())
        result = ExternalValueSyncResult()
        current_token = self.active_session_store.snapshot_token()
        if current_token is None:
            self._active_session_token_seen = None
            self._pending_external_values.clear()
            return result

        if current_token != self._active_session_token_seen:
            try:
                external_state = self.active_session_store.load()
            except ValueError as exc:
                LOGGER.warning("Falha ao sincronizar valores externos: %s", exc)
                return result
            self._import_external_snapshot(
                external_state,
                protected_line_ids=protected_line_ids,
                resolved_line_ids=resolved_line_ids,
                result=result,
            )
            self._active_session_token_seen = current_token
        else:
            self._prune_pending_external_values(resolved_line_ids)

        self._apply_pending_external_values(
            protected_line_ids=protected_line_ids,
            resolved_line_ids=resolved_line_ids,
            result=result,
        )
        if result.has_changes:
            self._recompute()
        return result

    def _import_external_snapshot(
        self,
        external_state: AppState,
        *,
        protected_line_ids: set[str],
        resolved_line_ids: set[str],
        result: ExternalValueSyncResult,
    ) -> None:
        current_lines = self._line_lookup(self.state.blocks)
        external_values = self._line_value_lookup(external_state.blocks)
        self._prune_pending_external_values(resolved_line_ids, current_lines=current_lines)
        for line_id, external_value in external_values.items():
            current_line_info = current_lines.get(line_id)
            if current_line_info is None:
                continue
            if line_id in resolved_line_ids:
                self._pending_external_values.pop(line_id, None)
                continue
            block_id, page_id, line = current_line_info
            if line_id in protected_line_ids:
                if line.value != external_value:
                    self._pending_external_values[line_id] = external_value
                else:
                    self._pending_external_values.pop(line_id, None)
                continue
            self._set_line_value_from_external(result, block_id, page_id, line_id, line, external_value)
            self._pending_external_values.pop(line_id, None)

    def _apply_pending_external_values(
        self,
        *,
        protected_line_ids: set[str],
        resolved_line_ids: set[str],
        result: ExternalValueSyncResult,
    ) -> None:
        if not self._pending_external_values:
            return
        current_lines = self._line_lookup(self.state.blocks)
        for line_id in list(self._pending_external_values):
            if line_id in resolved_line_ids or line_id not in current_lines:
                self._pending_external_values.pop(line_id, None)
                continue
            if line_id in protected_line_ids:
                continue
            block_id, page_id, line = current_lines[line_id]
            external_value = self._pending_external_values.pop(line_id)
            self._set_line_value_from_external(result, block_id, page_id, line_id, line, external_value)

    def _set_line_value_from_external(
        self,
        result: ExternalValueSyncResult,
        block_id: str,
        page_id: str,
        line_id: str,
        line: BetLine,
        external_value: Decimal | None,
    ) -> None:
        if line.value == external_value:
            return
        line.value = external_value
        result.line_ids.add(line_id)
        result.page_ids.add(page_id)
        result.block_ids.add(block_id)

    def _overlay_line_values_on_state(self, state: AppState, values: dict[str, Decimal | None]) -> None:
        line_lookup = self._line_lookup(state.blocks)
        for line_id, value in values.items():
            line_info = line_lookup.get(line_id)
            if line_info is None:
                continue
            line_info[2].value = value

    def _prune_pending_external_values(
        self,
        resolved_line_ids: set[str],
        *,
        current_lines: dict[str, tuple[str, str, BetLine]] | None = None,
    ) -> None:
        if not self._pending_external_values:
            return
        current_lines = current_lines or self._line_lookup(self.state.blocks)
        for line_id in list(self._pending_external_values):
            if line_id in resolved_line_ids or line_id not in current_lines:
                self._pending_external_values.pop(line_id, None)

    def _ensure_trailing_blank_line(self, page: Page) -> None:
        if not page.lines:
            page.lines.append(self._new_line())
            return
        if not page.lines[-1].is_empty:
            page.lines.append(self._new_line())
        while len(page.lines) > 1 and page.lines[-1].is_empty and page.lines[-2].is_empty:
            page.lines.pop()

    def _renumber_pages(self, block: Block) -> None:
        for number, page in enumerate(block.pages, start=1):
            page.number = number

    def _guard_page_mutation(self, block: Block, page: Page, force_unlock: bool) -> None:
        if not is_page_locked(page):
            return
        if force_unlock:
            for line in page.lines:
                line.value = None
            return
        raise PageLockedError(
            page_id=page.page_id,
            page_number=page.number,
            block_number=block.number,
            message=(
                f"A p\u00e1gina {page.number} do bloco {block.number} est\u00e1 bloqueada. "
                "Desbloquear remover\u00e1 todos os valores informados nesta p\u00e1gina."
            ),
        )

    def _guard_block_mutation(self, block: Block, force_unlock: bool) -> None:
        if not block.money_locked:
            return
        if force_unlock:
            block.money_locked = False
            return
        raise BlockLockedError(
            block_id=block.block_id,
            block_number=block.number,
            message=(
                f"O bloco {block.number} est\u00e1 bloqueado porque o dinheiro j\u00e1 foi informado. "
                "Desbloqueie o bloco para fazer altera\u00e7\u00f5es."
            ),
        )

    def _guard_block_pages_mutation(self, block: Block, force_unlock: bool) -> None:
        for page in block.pages:
            if is_page_locked(page):
                self._guard_page_mutation(block, page, force_unlock)
