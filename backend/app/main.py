"""Сборка приложения FastAPI.

Создаёт приложение, подключает CORS, логирование, роутеры и инициализирует
WebSocket-инфраструктуру (менеджер, комнаты, Redis-шину).
"""

import asyncio
import logging

import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.ws.bus import RedisBus
from app.ws.lifecycle import cleanup_rooms
from app.ws.manager import ConnectionManager
from app.ws.rooms import RoomRegistry
from app.ws.state_store import StateStore
from app.ws.tokens import TokenStore
from app.ws.router import router as ws_router

logger = logging.getLogger("app")

ROOM_CLEANUP_INTERVAL = 30.0


async def _room_cleanup_loop(app: FastAPI) -> None:
    """Периодически чистит пустые и зависшие комнаты."""
    while True:
        await asyncio.sleep(ROOM_CLEANUP_INTERVAL)
        removed = cleanup_rooms(app.state.room_registry, app.state.connection_manager)
        if removed:
            logger.info("Очистка комнат, удалены: %s", removed)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Запуск: %s v%s", settings.app_name, settings.app_version)

    connection_manager = ConnectionManager()
    room_registry = RoomRegistry()
    redis_bus = RedisBus(settings.redis_url, connection_manager)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    token_store = TokenStore(redis_client)
    state_store = StateStore(redis_client)

    app.state.connection_manager = connection_manager
    app.state.room_registry = room_registry
    app.state.redis_bus = redis_bus
    app.state.token_store = token_store
    app.state.state_store = state_store

    await redis_bus.start()
    logger.info("Redis Pub/Sub шина запущена")

    cleanup_task = asyncio.create_task(_room_cleanup_loop(app))
    logger.info("Фоновая очистка комнат запущена")

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    await redis_client.aclose()
    await redis_bus.stop()
    logger.info("Остановка приложения")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(ws_router)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"app": settings.app_name, "docs": "/docs", "health": "/health"}

    return app


app = create_app()