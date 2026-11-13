"""Тесты модели комнаты (лобби)."""

import pytest

from app.ws.rooms import Player, RoomRegistry, RoomStatus, generate_room_code


def test_generate_room_code() -> None:
    for _ in range(50):
        code = generate_room_code()
        assert len(code) == 6
        assert code.isalnum()
        assert not any(ch in code for ch in "O0I1")


def test_create_room_adds_host() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    assert room.host_id == "h"
    assert room.status is RoomStatus.WAITING
    assert len(room.players) == 1
    assert room.players["h"].is_host is True


def test_create_room_validates_players() -> None:
    registry = RoomRegistry()
    with pytest.raises(ValueError):
        registry.create(host_id="h", host_name="Х", max_players=2)
    with pytest.raises(ValueError):
        registry.create(host_id="h", host_name="Х", max_players=8)


def test_is_full_and_can_start() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=3)
    assert not room.can_start  # только хост
    room.add_player(Player(id="a", name="Аня"))
    assert not room.can_start  # 2 игрока
    room.add_player(Player(id="b", name="Боря"))
    assert room.can_start  # 3 игрока
    assert room.is_full


def test_remove_player_and_empty() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    room.add_player(Player(id="a", name="Аня"))
    room.remove_player("a")
    assert "a" not in room.players
    assert not room.is_empty
    room.remove_player("h")
    assert room.is_empty


def test_registry_remove() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    registry.remove(room.code)
    assert registry.get(room.code) is None