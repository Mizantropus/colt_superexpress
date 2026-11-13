"""Менеджер WebSocket-подключений (в пределах одного процесса)."""

from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # player_id -> WebSocket
        self._connections: dict[str, WebSocket] = {}
        # player_id -> room_code
        self._membership: dict[str, str] = {}

    async def connect(self, player_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[player_id] = ws

    def disconnect_ws(self, player_id: str) -> None:
        """Убирает WS-подключение, сохраняя членство в комнате (для реконнекта)."""
        self._connections.pop(player_id, None)

    def room_of(self, player_id: str) -> str | None:
        return self._membership.get(player_id)

    def set_room(self, player_id: str, room_code: str) -> None:
        self._membership[player_id] = room_code

    def clear_room(self, player_id: str) -> None:
        self._membership.pop(player_id, None)

    def players_in_room(self, room_code: str) -> list[str]:
        return [pid for pid, code in self._membership.items() if code == room_code]

    async def send_to_player(self, player_id: str, message: dict) -> None:
        ws = self._connections.get(player_id)
        if ws is not None:
            await ws.send_json(message)

    async def broadcast_to_room(self, room_code: str, message: dict) -> None:
        for player_id in self.players_in_room(room_code):
            ws = self._connections.get(player_id)
            if ws is not None:
                await ws.send_json(message)