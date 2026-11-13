"""Тесты протокола (валидация)."""

from app.game.models import Action
from app.ws.protocol import (
    decode,
    error_message,
    make_message,
    parse_actions,
    parse_max_players,
    parse_player_name,
    parse_room_code,
)


def test_make_and_decode() -> None:
    assert make_message("pong", value=1) == {"type": "pong", "value": 1}
    assert decode('{"type": "ping"}') == {"type": "ping"}


def test_error_message() -> None:
    assert error_message("bad_message", "ошибка") == {
        "type": "error", "code": "bad_message", "message": "ошибка"}


def test_parse_max_players() -> None:
    assert parse_max_players({"max_players": 5}) == 5
    assert parse_max_players({"max_players": "4"}) == 4
    assert parse_max_players({"max_players": 2}) is None
    assert parse_max_players({"max_players": 9}) is None
    assert parse_max_players({}) is None


def test_parse_actions() -> None:
    assert parse_actions({"actions": ["move", "shoot", "horse"]}) == [Action.MOVE, Action.SHOOT, Action.HORSE]
    assert parse_actions({"actions": ["move"]}) is None
    assert parse_actions({"actions": ["move", "shoot", "bogus"]}) is None
    assert parse_actions({"actions": "notalist"}) is None


def test_parse_name_and_code() -> None:
    assert parse_player_name({"player_name": "Аня"}) == "Аня"
    assert parse_player_name({}) == "Игрок"
    assert parse_room_code({"room_code": " abc "}) == "ABC"