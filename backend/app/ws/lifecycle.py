"""Жизненный цикл комнаты (чистая логика, без WebSocket)."""

from __future__ import annotations

import time

from app.ws.rooms import Player, Room, RoomRegistry

RECONNECT_GRACE_SECONDS = 60


def leave_room(room: Room, player_id: str) -> Player | None:
    """Игрок покидает комнату; при уходе хоста права передаются другому."""
    player = room.remove_player(player_id)
    if player is None:
        return None
    if player.is_host and room.players:
        new_host = next(iter(room.players.values()))
        new_host.is_host = True
        room.host_id = new_host.id
    return player


def disconnect_player(room: Room, player_id: str, now: float | None = None) -> bool:
    """Помечает игрока отключённым, сохраняя его место в комнате."""
    player = room.players.get(player_id)
    if player is None:
        return False
    player.connected = False
    player.disconnected_at = now if now is not None else time.time()
    return True


def reconnect_player(room: Room, player_id: str) -> bool:
    """Возвращает игрока в подключённое состояние."""
    player = room.players.get(player_id)
    if player is None or player.connected:
        return False
    player.connected = True
    player.disconnected_at = None
    return True


def cleanup_rooms(registry: RoomRegistry, now: float | None = None) -> list[str]:
    """Удаляет отключившихся сверх grace-периода игроков и пустые комнаты.

    Возвращает коды удалённых комнат.
    """
    now = now if now is not None else time.time()
    removed: list[str] = []
    for room in registry.rooms():
        for player_id in list(room.players):
            player = room.players[player_id]
            if (
                not player.connected
                and player.disconnected_at is not None
                and (now - player.disconnected_at) > RECONNECT_GRACE_SECONDS
            ):
                leave_room(room, player_id)
        if room.is_empty:
            registry.remove(room.code)
            removed.append(room.code)
    return removed