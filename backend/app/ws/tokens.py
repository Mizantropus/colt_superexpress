"""Анонимная идентичность: player_token."""

from __future__ import annotations

import secrets

TOKEN_BYTES = 32


def generate_token() -> str:
    """Генерирует случайный неудоставаемый токен (64 hex-символа)."""
    return secrets.token_hex(TOKEN_BYTES)


class TokenStore:
    """Хранит соответствие token -> player_id.

    backend — объект с асинхронными get/set/delete (Redis в проде,
    заглушка в тестах).
    """

    PREFIX = "player:token:"

    def __init__(self, backend) -> None:
        self._backend = backend

    async def issue(self, player_id: str) -> str:
        token = generate_token()
        await self._backend.set(self.PREFIX + token, player_id)
        return token

    async def resolve(self, token: str) -> str | None:
        value = await self._backend.get(self.PREFIX + token)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode()
        return value

    async def revoke(self, token: str) -> None:
        await self._backend.delete(self.PREFIX + token)