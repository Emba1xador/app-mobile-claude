from __future__ import annotations

from decimal import Decimal

import pytest

from core.finance_engine import block_total, block_value_progress
from core.enums import BetType, CommitMode, Flag
from core.page_lock import BlockLockedError
from services.controller import BancaController


def _add_second_line(controller: BancaController, line_id: str) -> str:
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    return controller.state.blocks[0].pages[0].lines[1].line_id


def test_apply_flag_multiple_lines(tmp_path):
    controller = BancaController(tmp_path)
    _, _, first_line = controller.create_block("452")
    second_line = _add_second_line(controller, first_line)
    controller.upsert_bet_text(second_line, "666", commit_mode=CommitMode.ENTER)

    controller.apply_flag([first_line, second_line], Flag.DE)

    page = controller.state.blocks[0].pages[0]
    assert Flag.DE in page.lines[0].spec.flags
    assert Flag.DE in page.lines[1].spec.flags


def test_apply_flag_invalid_is_ignored(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "68/", commit_mode=CommitMode.ENTER)

    controller.apply_flag([line_id], Flag.INVERTIDA)

    assert controller.state.blocks[0].pages[0].lines[0].spec.flags == []


def test_apply_flag_add_mode_does_not_toggle_existing_flag(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)

    controller.apply_flag([line_id], Flag.DE, mode="add")
    controller.apply_flag([line_id], Flag.DE, mode="add")

    assert controller.state.blocks[0].pages[0].lines[0].spec.flags == [Flag.DE]


def test_clear_flags_removes_all_flags(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "C 524 I.V DE", commit_mode=CommitMode.ENTER)

    controller.clear_flags([line_id])

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.flags == []
    assert line.spec.normalized_text == "C 524"


def test_transform_lines_preserves_flags_between_m_and_mc(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "MC 2145 DE", commit_mode=CommitMode.ENTER)

    controller.transform_lines([line_id], BetType.MILHAR)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.MILHAR
    assert line.spec.numbers == ["2145"]
    assert line.spec.flags == [Flag.DE]


def test_shift_commit_promotes_milhar_with_flags_to_mc(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")

    controller.upsert_bet_text(line_id, "M 6542 I.V", commit_mode=CommitMode.SHIFT_MC)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.MILHAR_CENTENA
    assert line.spec.flags == [Flag.INVERTIDA]
    assert line.raw_text == "MC 6542 I.V"


def test_toggle_mc_preserves_existing_flags(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "M 6542 DE I.V", commit_mode=CommitMode.ENTER)

    controller.toggle_mc([line_id])

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.MILHAR_CENTENA
    assert line.spec.flags == [Flag.DE, Flag.INVERTIDA]
    assert line.raw_text == "MC 6542 DE I.V"


def test_resolve_flag_input_preserves_mc_type_on_canonical_text(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "6542", commit_mode=CommitMode.SHIFT_MC)

    resolved = controller.resolve_flag_input("MC 6542", Flag.INVERTIDA)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.MILHAR_CENTENA
    assert line.raw_text == "MC 6542"
    assert resolved == "MC 6542 I.V"


def test_transform_lines_ignores_incompatible_target(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "1234", commit_mode=CommitMode.ENTER)

    controller.transform_lines([line_id], BetType.CENTENA)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.MILHAR


def test_transform_error_line_uses_numeric_groups(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "xx 12 24 25", commit_mode=CommitMode.ENTER)

    controller.transform_lines([line_id], BetType.TERNO_GRUPO)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.bet_type == BetType.TERNO_GRUPO
    assert line.spec.normalized_text == "TG 12 24 25"


def test_invalid_line_cannot_receive_value(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "entrada invalida", commit_mode=CommitMode.ENTER)

    with pytest.raises(ValueError):
        controller.set_line_value(line_id, "10")


def test_apply_value_to_page_ignores_invalid_lines(tmp_path):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "erro livre", commit_mode=CommitMode.ENTER)

    controller.apply_value_to_page(page_id, "2")

    page = controller.state.blocks[0].pages[0]
    assert page.lines[0].value == Decimal("2.00")
    assert page.lines[1].value is None


def test_apply_value_to_pending_lines_preserves_existing_values(tmp_path):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "666", commit_mode=CommitMode.ENTER)
    controller.set_line_value(line_id, "10")

    controller.apply_value_to_pending_lines(page_id, "2")

    page = controller.state.blocks[0].pages[0]
    assert page.lines[0].value == Decimal("10.00")
    assert page.lines[1].value == Decimal("2.00")


def test_create_block_rejects_non_numeric_value(tmp_path):
    controller = BancaController(tmp_path)

    with pytest.raises(ValueError):
        controller.create_block("abc")

    with pytest.raises(ValueError):
        controller.create_block("")


def test_money_lock_blocks_sensitive_changes(tmp_path):
    controller = BancaController(tmp_path)
    block_id, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_block_money(block_id, "10")

    with pytest.raises(BlockLockedError):
        controller.insert_line_below(line_id)


def test_money_lock_blocks_value_changes_and_page_fill(tmp_path):
    controller = BancaController(tmp_path)
    block_id, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_line_value(line_id, "10")
    controller.set_block_money(block_id, "100")

    with pytest.raises(BlockLockedError):
        controller.set_line_value(line_id, "20")

    with pytest.raises(BlockLockedError):
        controller.apply_value_to_page(page_id, "30")


def test_money_lock_can_be_forced_for_value_change(tmp_path):
    controller = BancaController(tmp_path)
    block_id, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_line_value(line_id, "10")
    controller.set_block_money(block_id, "100")

    controller.set_line_value(line_id, "20", force_unlock=True)
    controller.apply_value_to_page(page_id, "30", force_unlock=True)

    assert controller.state.blocks[0].money_locked is False
    assert controller.state.blocks[0].pages[0].lines[0].value == Decimal("30.00")


def test_finance_totals_panel_data(tmp_path):
    controller = BancaController(tmp_path)
    block_id, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_line_value(line_id, "100")
    controller.set_block_money(block_id, "100")
    controller.set_total_paid_prizes("30")
    controller.set_session_notes("Fechamento adiado")

    totals = controller.get_finance_totals_data()

    assert Decimal(totals["total_received"]) == Decimal("100.00")
    assert Decimal(totals["total_bruto"]) == Decimal("100.00")
    assert Decimal(totals["total_liquido"]) == Decimal("70.00")
    assert Decimal(totals["cash_balance"]) == Decimal("70.00")
    assert totals["session_notes"] == "Fechamento adiado"


def test_session_name_is_trimmed(tmp_path):
    controller = BancaController(tmp_path)

    controller.set_session_name("  Matriz manha  ")

    assert controller.state.session_name == "Matriz manha"


def test_external_mobile_sync_updates_other_lines_and_defers_protected_one(tmp_path):
    desktop = BancaController(tmp_path)
    _, _, first_line_id = desktop.create_block("452")
    desktop.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = desktop.state.blocks[0].pages[0].lines[1].line_id
    desktop.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)

    mobile = BancaController(tmp_path)
    mobile.set_line_value(first_line_id, "10")
    mobile.set_line_value(second_line_id, "20")

    first_sync = desktop.sync_external_mobile_values_if_needed({second_line_id})
    second_sync = desktop.sync_external_mobile_values_if_needed()

    assert desktop.state.blocks[0].pages[0].lines[0].value == Decimal("10.00")
    assert desktop.state.blocks[0].pages[0].lines[1].value == Decimal("20.00")
    assert first_sync.line_ids == {first_line_id}
    assert second_sync.line_ids == {second_line_id}


def test_unrelated_desktop_save_merges_mobile_value_before_persist(tmp_path):
    desktop = BancaController(tmp_path)
    _, _, first_line_id = desktop.create_block("452")
    desktop.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = desktop.state.blocks[0].pages[0].lines[1].line_id
    desktop.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)
    third_line_id = desktop.state.blocks[0].pages[0].lines[2].line_id
    desktop.upsert_bet_text(third_line_id, "777", commit_mode=CommitMode.ENTER)

    mobile = BancaController(tmp_path)
    mobile.set_line_value(second_line_id, "20")

    desktop.set_session_notes("edicao local irrelevante")
    restored = BancaController(tmp_path)
    restored_block = restored.state.blocks[0]

    assert restored_block.pages[0].lines[1].value == Decimal("20.00")
    assert block_value_progress(restored_block) == (1, 3)
    assert block_total(restored_block) == Decimal("20.00")


def test_protected_external_value_survives_local_save_and_applies_after_release(tmp_path):
    desktop = BancaController(tmp_path)
    _, _, first_line_id = desktop.create_block("452")
    desktop.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = desktop.state.blocks[0].pages[0].lines[1].line_id
    desktop.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)

    mobile = BancaController(tmp_path)
    mobile.set_line_value(second_line_id, "20")

    first_sync = desktop.sync_external_mobile_values_if_needed({second_line_id})
    assert desktop.state.blocks[0].pages[0].lines[1].value is None
    desktop.set_session_notes("save local sem relacao", protected_line_ids={second_line_id})
    restored = BancaController(tmp_path)
    second_sync = desktop.sync_external_mobile_values_if_needed()

    assert first_sync.has_changes is False
    assert desktop.state.blocks[0].pages[0].lines[1].value == Decimal("20.00")
    assert restored.state.blocks[0].pages[0].lines[1].value == Decimal("20.00")
    assert second_sync.line_ids == {second_line_id}


def test_save_session_preserves_external_value_and_totals(tmp_path):
    desktop = BancaController(tmp_path)
    _, _, first_line_id = desktop.create_block("452")
    desktop.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = desktop.state.blocks[0].pages[0].lines[1].line_id
    desktop.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)

    mobile = BancaController(tmp_path)
    mobile.set_line_value(second_line_id, "20")

    save_path = desktop.save_session()
    active_restored = BancaController(tmp_path)
    saved_state = desktop.store.load(save_path)

    assert active_restored.state.blocks[0].pages[0].lines[1].value == Decimal("20.00")
    assert saved_state.blocks[0].pages[0].lines[1].value == Decimal("20.00")
    assert block_value_progress(active_restored.state.blocks[0]) == (1, 2)
    assert block_total(active_restored.state.blocks[0]) == Decimal("20.00")


def test_percentage_stays_fixed_at_seventy_percent(tmp_path):
    controller = BancaController(tmp_path)

    controller.set_percentage("55")

    assert controller.state.percentage == Decimal("0.70")


def test_resolve_flag_input_preserves_numbers(tmp_path):
    controller = BancaController(tmp_path)

    resolved = controller.resolve_flag_input("555", Flag.DE)

    assert resolved == "C 555 DE"


def test_session_overview_without_result_lists_blocks(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)

    overview = controller.get_session_overview_data()

    assert overview["result_loaded"] is False
    assert overview["selected_block_id"] == ""
    assert overview["awarded_blocks"] == []
    assert len(overview["blocks"]) == 1
    assert overview["blocks"][0]["block_id"] == controller.state.blocks[0].block_id
    assert overview["blocks"][0]["block_number"] == "452"
    assert overview["blocks"][0]["page_count"] == 1
    assert overview["blocks"][0]["bet_count"] == 1
    assert overview["blocks"][0]["prize_count"] == 0
    assert overview["blocks"][0]["pending_count"] == 3


def test_session_overview_with_result_lists_only_awarded_blocks(tmp_path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "M 6554", commit_mode=CommitMode.ENTER)
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])

    overview = controller.get_session_overview_data()
    awarded = overview["awarded_blocks"]

    assert overview["result_loaded"] is True
    assert len(awarded) == 1
    assert awarded[0]["block_number"] == "452"
    assert awarded[0]["prize_count"] == 1
    assert awarded[0]["details"][0]["text"].endswith("1° prêmio")


def test_operational_pendencies_use_new_grouped_labels(tmp_path):
    controller = BancaController(tmp_path)
    block_id, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_block_money(block_id, "")
    controller.upsert_bet_text(controller.state.blocks[0].pages[0].lines[1].line_id, "erro livre", commit_mode=CommitMode.ENTER)

    pendencies = controller.get_operational_pendencies()

    assert pendencies["ready_message"] == "Hor\u00e1rio pronto para fechamento."
    assert pendencies["groups"] == [
        {
            "group_id": "session",
            "title": "Sess\u00e3o",
            "critical_count": 1,
            "warning_count": 0,
            "total_count": 1,
            "tone": "critical",
            "items": ["Resultado n\u00e3o informado"],
        },
        {
            "group_id": f"block:{block_id}",
            "title": "Bloco 452",
            "critical_count": 3,
            "warning_count": 1,
            "total_count": 4,
            "tone": "critical",
            "items": [
                "Dinheiro n\u00e3o informado",
                "Contato n\u00e3o configurado",
                "P\u00e1gina 1 pendente",
                "P\u00e1gina 1 com aposta inv\u00e1lida",
            ],
        },
    ]
