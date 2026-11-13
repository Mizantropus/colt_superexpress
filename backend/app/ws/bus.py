"""Redis Pub/Sub шина для рассылки по комнатам.

Каждый процесс публикует сообщение в канал `colt:room:<code>`, а подписчик
(по паттерну `colt:room:*`) получает его и рассылает всем локальным
подключениям этой комнаты. Так рассылка работает и при нескольких воркерах.
"""

from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger("app.ws.bus")

CHANNEL_PREFIX = "colt:room:"
PATTERN = "colt:room:*"


def room_channel(room_code: str) -> str:
    return CHANNEL_PREFIX + room_code


class RedisBus:
    def __init__(self, redis_url: str, manager) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._manager = manager
        self._pubsub = self._redis.pubsub()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        await self._pubsub.psubscribe(PATTERN)
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._pubsub.aclose()
        await self._redis.aclose()

    async def publish(self, room_code: str, message: dict) -> None:
        await self._redis.publish(room_channel(room_code), json.dumps(message, ensure_ascii=False))

    async def _listen(self) -> None:
        while True:
            event = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if event is None:
                continue
            if event.get("type") != "pmessage":
                continue
            channel = event.get("channel")
            if not isinstance(channel, str) or not channel.startswith(CHANNEL_PREFIX):
                continue
            room_code = channel[len(CHANNEL_PREFIX):]
            raw = event.get("data")
            if not isinstance(raw, str):
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Невалидный JSON в шине, канал %s", channel)
                continue
            await self._manager.broadcast_to_room(room_code, message)