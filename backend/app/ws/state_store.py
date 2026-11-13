"""Хранилище состояния партии (Redis)."""

from __future__ import annotations

import json

from app.game.serialization import state_from_dict, state_to_dict
from app.game.state import GameState


class StateStore:
    """Сохраняет/загружает GameState в Redis (для восстановления после рестарта)."""

    PREFIX = "room:state:"

    def __init__(self, backend) -> None:
        self._backend = backend

    async def save(self, room_code: str, state: GameState) -> None:
        payload = json.dumps(state_to_dict(state), ensure_ascii=False)
        await self._backend.set(self.PREFIX + room_code, payload)

    async def load(self, room_code: str) -> GameState | None:
        raw = await self._backend.get(self.PREFIX + room_code)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        return state_from_dict(json.loads(raw))

    async def delete(self, room_code: str) -> None:
        await self._backend.delete(self.PREFIX + room_code)