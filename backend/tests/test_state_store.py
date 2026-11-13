"""Тесты хранилища состояния."""

import asyncio
import random

from app.game.setup import setup_game
from app.ws.state_store import StateStore


class _FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def set(self, key, value) -> None:
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key) -> None:
        self.data.pop(key, None)


def test_state_store_roundtrip() -> None:
    backend = _FakeRedis()
    store = StateStore(backend)
    state = setup_game(
        [("p0", "P0"), ("p1", "P1"), ("p2", "P2")],
        first_player_id="p0", rng=random.Random(0),
    )

    async def scenario():
        await store.save("ABC123", state)
        loaded = await store.load("ABC123")
        assert loaded is not None
        assert loaded.round_number == state.round_number
        assert len(loaded.bandits) == 3
        await store.delete("ABC123")
        assert await store.load("ABC123") is None

    asyncio.run(scenario())