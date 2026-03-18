from core.entities import BetLine
from core.parser import parse_bet_input
from core.result_engine import build_result_snapshot, evaluate_line


RESULT = build_result_snapshot(["5878", "9685", "9758", "3217", "1547"])


def line_for(text: str) -> BetLine:
    return BetLine(line_id="line", raw_text=text, spec=parse_bet_input(text))


def test_centena_wins():
    winners = evaluate_line(line_for("C 878"), RESULT)
    assert winners
    assert winners[0].prize_label == "1°"


def test_mc_de_matches_centenas_from_rotations():
    winners = evaluate_line(line_for("MC 5878 DE"), RESULT)
    assert winners


def test_milhar_invertida_can_win_with_first_digit_last():
    custom_result = build_result_snapshot(["9652", "0000", "0000", "0000", "0000"])
    winners = evaluate_line(line_for("M 2965 I.V"), custom_result)
    assert winners


def test_duque_same_slot():
    custom_result = build_result_snapshot(["2525", "6868", "0000", "1111", "2222"])
    winners = evaluate_line(line_for("DD 25 68 DE"), custom_result)
    assert winners


def test_group_detection():
    winners = evaluate_line(line_for("G 22"), RESULT)
    assert winners


def test_group_compact_input_detection():
    winners = evaluate_line(line_for("g22"), RESULT)
    assert winners


def test_closure_alias_detection():
    custom_result = build_result_snapshot(["0333", "0000", "0000", "0000", "0000"])
    winners = evaluate_line(line_for("000 a 900"), custom_result)
    assert winners


def test_closure_accepts_de_flag():
    custom_result = build_result_snapshot(["3000", "0000", "0000", "0000", "0000"])
    winners = evaluate_line(line_for("F 000 / 900 DE"), custom_result)
    assert winners


def test_closure_accepts_invertida_flag():
    custom_result = build_result_snapshot(["0987", "0000", "0000", "0000", "0000"])
    winners = evaluate_line(line_for("F 789 / 789 I.V"), custom_result)
    assert winners
