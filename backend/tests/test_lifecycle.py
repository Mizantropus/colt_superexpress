"""Тесты жизненного цикла комнаты."""

from app.ws.lifecycle import (
    RECONNECT_GRACE_SECONDS,
    cleanup_rooms,
    disconnect_player,
    leave_room,
    reconnect_player,
)
from app.ws.rooms import Player, RoomRegistry


def _room():
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    room.add_player(Player(id="a", name="Аня"))
    return registry, room


def test_leave_player() -> None:
    registry, room = _room()
    player = leave_room(room, "a")
    assert player is not None and player.id == "a"
    assert "a" not in room.players
    assert not room.is_empty  # хост остался


def test_leave_host_transfers() -> None:
    registry, room = _room()
    left = leave_room(room, "h")
    assert left is not None and left.is_host is True
    assert room.host_id == "a"
    assert room.players["a"].is_host is True


def test_disconnect_and_reconnect() -> None:
    registry, room = _room()
    assert disconnect_player(room, "a", now=1000) is True
    assert room.players["a"].connected is False
    assert room.players["a"].disconnected_at == 1000
    assert reconnect_player(room, "a") is True
    assert room.players["a"].connected is True
    assert room.players["a"].disconnected_at is None


def test_cleanup_removes_stale_and_empty() -> None:
    registry, room = _room()
    disconnect_player(room, "a", now=1000)
    disconnect_player(room, "h", now=1000)
    now = 1000 + RECONNECT_GRACE_SECONDS + 1
    removed = cleanup_rooms(registry, now=now)
    assert room.code in removed
    assert registry.get(room.code) is None


def test_cleanup_keeps_recent_disconnect() -> None:
    registry, room = _room()
    disconnect_player(room, "a", now=1000)
    removed = cleanup_rooms(registry, now=1000 + 1)
    assert room.code not in removed
    assert "a" in room.players