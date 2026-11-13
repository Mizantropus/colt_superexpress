"""Тесты ядра WebSocket-слоя (без сети): протокол и комнаты."""

from app.ws.protocol import decode, make_message
from app.ws.rooms import Player, RoomRegistry, generate_room_code


def test_make_message_and_decode() -> None:
    message = make_message("pong", value=42)
    assert message == {"type": "pong", "value": 42}
    assert decode('{"type": "ping"}') == {"type": "ping"}


def test_room_code_format() -> None:
    for _ in range(50):
        code = generate_room_code()
        assert len(code) == 6
        assert code.isalnum()
        assert not any(ch in code for ch in "O0I1")


def test_registry_create_and_remove() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    assert registry.get(room.code) is room
    assert room.host_id == "h"
    assert len(room.players) == 1  # хост уже в комнате
    registry.remove(room.code)
    assert registry.get(room.code) is None


def test_room_players() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    room.add_player(Player(id="a", name="Аня"))
    room.add_player(Player(id="b", name="Боря"))
    assert len(room.players) == 3  # хост + 2
    removed = room.remove_player("a")
    assert removed is not None and removed.name == "Аня"
    assert not room.is_empty
    room.remove_player("b")
    assert not room.is_empty  # хост остался
    room.remove_player("h")
    assert room.is_empty