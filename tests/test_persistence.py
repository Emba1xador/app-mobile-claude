from pathlib import Path

from decimal import Decimal

import pytest

from core.enums import Flag
from services.controller import BancaController


def test_save_and_load_roundtrip(tmp_path: Path):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.set_session_name("Sessao da matriz")
    controller.upsert_bet_text(line_id, "d85", commit_mode="enter")
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "000 a 900", commit_mode="enter")
    controller.set_line_value(line_id, "2")
    controller.set_result(["5878", "9685", "9758", "3217", "1547"])
    controller.set_block_money(controller.state.blocks[0].block_id, "10")
    controller.set_total_paid_prizes("4")
    controller.set_session_notes("Movimento forte no 2\u00ba hor\u00e1rio")
    controller.state.percentage = Decimal("0.55")
    controller.set_block_whatsapp(controller.state.blocks[0].block_id, "11999999999")

    save_path = controller.save_session()

    loaded = BancaController(tmp_path)
    loaded.load_session(save_path)

    assert loaded.state.blocks[0].number == "452"
    assert loaded.state.blocks[0].pages[0].lines[0].value is not None
    assert loaded.state.blocks[0].pages[0].lines[0].spec.normalized_text == "D 85"
    assert loaded.state.blocks[0].pages[0].lines[1].spec.normalized_text == "F 000 / 900"
    assert loaded.state.blocks[0].whatsapp_phone == "11999999999"
    assert loaded.state.result is not None
    assert loaded.state.session_name == "Sessao da matriz"
    assert loaded.state.total_paid_prizes is not None
    assert loaded.state.session_notes == "Movimento forte no 2\u00ba hor\u00e1rio"
    assert loaded.state.percentage == Decimal("0.70")
    assert loaded.state.blocks[0].money_locked is True


def test_save_session_generates_unique_default_names(tmp_path: Path):
    controller = BancaController(tmp_path)
    controller.create_block("452")

    first = controller.save_session()
    second = controller.save_session()

    assert first != second


def test_invalid_save_raises_friendly_error(tmp_path: Path):
    controller = BancaController(tmp_path)
    invalid_path = tmp_path / "saves" / "broken.json"
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_text("{ invalido", encoding="utf-8")

    with pytest.raises(ValueError, match="corrompido, inválido ou incompatível"):
        controller.load_session(invalid_path)


def test_corrupted_whatsapp_map_is_ignored_safely(tmp_path: Path):
    (tmp_path / "banca_whatsapp_map.json").write_text("{ invalido", encoding="utf-8")

    controller = BancaController(tmp_path)

    assert controller.state.whatsapp_map == {}


def test_save_and_load_preserve_milhar_flags_and_mc_type(tmp_path: Path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "M 6542 DE", commit_mode="enter")
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "6542", commit_mode="shift_mc")
    controller.apply_flag([second_line], Flag.INVERTIDA)

    save_path = controller.save_session()

    loaded = BancaController(tmp_path)
    loaded.load_session(save_path)

    first = loaded.state.blocks[0].pages[0].lines[0]
    second = loaded.state.blocks[0].pages[0].lines[1]
    assert first.spec.bet_type.value == "M"
    assert [flag.value for flag in first.spec.flags] == ["DE"]
    assert first.raw_text == "M 6542 DE"
    assert second.spec.bet_type.value == "MC"
    assert [flag.value for flag in second.spec.flags] == ["I.V"]
    assert second.raw_text == "MC 6542 I.V"


def test_session_name_persists_in_active_session(tmp_path: Path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao da tarde")

    restored = BancaController(tmp_path)

    assert restored.state.session_name == "Operacao da tarde"


def test_restore_active_session_can_be_opt_in(tmp_path: Path):
    controller = BancaController(tmp_path)
    controller.set_session_name("Operacao da tarde")

    blank = BancaController(tmp_path, restore_active_session=False)

    assert blank.state.session_name == ""
    assert blank.has_resumable_active_session() is True

    assert blank.restore_active_session() is True
    assert blank.state.session_name == "Operacao da tarde"


def test_end_session_saves_and_clears_active_runtime(tmp_path: Path):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "d85", commit_mode="enter")
    controller.set_session_name("Fechamento da tarde")

    save_path = controller.end_session()

    assert save_path is not None
    assert save_path.exists()
    assert controller.active_session_store.exists() is False
    assert controller.state.blocks == []
    assert controller.state.session_name == ""
    assert controller.has_meaningful_session() is False

    reopened = BancaController(tmp_path, restore_active_session=False)

    assert reopened.has_resumable_active_session() is False
