from core.enums import BetType, CommitMode, Flag
from core.parser import expand_closure, milhar_iv_permutations, parse_bet_input


def test_auto_centena_and_milhar():
    centena = parse_bet_input("555")
    milhar = parse_bet_input("1234")
    mc = parse_bet_input("1234", commit_mode=CommitMode.SHIFT_MC)

    assert centena.bet_type == BetType.CENTENA
    assert milhar.bet_type == BetType.MILHAR
    assert mc.bet_type == BetType.MILHAR_CENTENA


def test_shortcuts_are_parsed():
    assert parse_bet_input("68/").bet_type == BetType.DEZENA
    assert parse_bet_input("d85").normalized_text == "D 85"
    assert parse_bet_input("/85").normalized_text == "D 85"
    assert parse_bet_input("85/").normalized_text == "D 85"
    assert parse_bet_input("85/59").bet_type == BetType.DUQUE_DEZENA
    assert parse_bet_input("85/59/87").bet_type == BetType.TERNO_DEZENA
    assert parse_bet_input("000/999").normalized_text == "F 000 / 999"
    assert parse_bet_input("000 a 900").normalized_text == "F 000 / 900"
    assert parse_bet_input("000 à 900").normalized_text == "F 000 / 900"
    assert parse_bet_input("000 Ã  900").normalized_text == "F 000 / 900"


def test_group_validation_and_flags():
    invalid = parse_bet_input("G 26")
    valid_group = parse_bet_input("g25")
    short_group = parse_bet_input("G 1")
    valid = parse_bet_input("C 524 I.V DE")
    milhar_de = parse_bet_input("M 6542 DE")
    mc_de = parse_bet_input("MC 6542 DE")
    closure = parse_bet_input("F 000 / 900 I.V DE")
    tg_slash = parse_bet_input("tg 5/9/10")
    tg_spaced = parse_bet_input("TG 5 9 10")
    tg_invalid = parse_bet_input("TG 5/9/26")

    assert invalid.bet_type == BetType.ERROR
    assert valid_group.bet_type == BetType.GRUPO
    assert valid_group.normalized_text == "G 25"
    assert short_group.normalized_text == "G 01"
    assert valid.flags == [Flag.INVERTIDA, Flag.DE]
    assert milhar_de.bet_type == BetType.MILHAR
    assert milhar_de.flags == [Flag.DE]
    assert milhar_de.normalized_text == "M 6542 DE"
    assert mc_de.bet_type == BetType.MILHAR_CENTENA
    assert mc_de.flags == [Flag.DE]
    assert closure.flags == [Flag.INVERTIDA, Flag.DE]
    assert tg_slash.bet_type == BetType.TERNO_GRUPO
    assert tg_slash.normalized_text == "TG 5 9 10"
    assert tg_spaced.normalized_text == "TG 5 9 10"
    assert tg_invalid.bet_type == BetType.ERROR


def test_milhar_invertida_generates_twelve():
    permutations = milhar_iv_permutations("2965")
    assert len(permutations) == 12
    assert "2965" in permutations
    assert "9652" in permutations


def test_expand_closure_special_case():
    assert expand_closure("000", "999") == [
        "000",
        "111",
        "222",
        "333",
        "444",
        "555",
        "666",
        "777",
        "888",
        "999",
    ]
