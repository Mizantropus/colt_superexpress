"""Тесты анонимной идентичности (токенов)."""

import asyncio

from app.ws.tokens import TokenStore, generate_token


class _FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    async def set(self, key, value) -> None:
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key) -> None:
        self.data.pop(key, None)


def test_generate_token() -> None:
    t1 = generate_token()
    t2 = generate_token()
    assert len(t1) == 64
    assert t1 != t2
    assert all(c in "0123456789abcdef" for c in t1)


def test_token_issue_resolve_revoke() -> None:
    backend = _FakeRedis()
    store = TokenStore(backend)

    async def scenario():
        token = await store.issue("p1")
        assert len(token) == 64
        assert await store.resolve(token) == "p1"
        await store.revoke(token)
        assert await store.resolve(token) is None

    asyncio.run(scenario())


def test_token_resolve_unknown() -> None:
    backend = _FakeRedis()
    store = TokenStore(backend)

    async def scenario():
        assert await store.resolve("unknown-token") is None

    asyncio.run(scenario())