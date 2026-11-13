"""WebSocket эндпоинт и диспетчеризация сообщений."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.game.planning import submit_plan
from app.game.serialization import public_state
from app.game.state import Phase
from app.game.setup import MAX_PLAYERS, MIN_PLAYERS
from app.ws import protocol
from app.ws.bus import RedisBus
from app.ws.lifecycle import disconnect_player, leave_room, reconnect_player
from app.ws.manager import ConnectionManager
from app.ws.rooms import Player, Room, RoomRegistry, RoomStatus
from app.ws.session import run_game, start_game
from app.ws.tokens import TokenStore

logger = logging.getLogger("app.ws")

_game_tasks: set = set()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    state = ws.app.state
    manager: ConnectionManager = state.connection_manager
    rooms: RoomRegistry = state.room_registry
    bus: RedisBus = state.redis_bus

    # Реконнект: клиент передаёт свой token в query-параметре.
    tokens: TokenStore = state.token_store
    token = ws.query_params.get("token")
    player_id = await tokens.resolve(token) if token else None
    if player_id is None:
        player_id = uuid.uuid4().hex
    await manager.connect(player_id, ws)

    # Если это известный игрок (реконнект) — помечаем подключённым.
    reconnect_code = manager.room_of(player_id)
    if reconnect_code is not None:
        reconnect_room = rooms.get(reconnect_code)
        if reconnect_room is None:
            # Стол удалён за время отсутствия — сбрасываем членство.
            manager.clear_room(player_id)
        elif reconnect_player(reconnect_room, player_id):
            await bus.publish(reconnect_code, protocol.make_message(
                protocol.ServerMessage.PLAYER_RECONNECTED, player_id=player_id))
            await manager.send_to_player(player_id, _resync_message(reconnect_room, player_id))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                message = protocol.decode(raw)
            except (ValueError, TypeError):
                await manager.send_to_player(
                    player_id,
                    protocol.make_message(
                        protocol.ServerMessage.ERROR,
                        code=protocol.ErrorCode.BAD_MESSAGE,
                        message="Сообщение должно быть JSON-объектом с полем 'type'",
                    ),
                )
                continue

            await _handle_message(player_id, manager, rooms, bus, tokens, message)
    except WebSocketDisconnect:
        pass
    finally:
        await _handle_disconnect(player_id, manager, rooms, bus)


async def _handle_message(player_id, manager, rooms, bus, tokens, message: dict) -> None:
    msg_type = message.get("type")

    if msg_type == protocol.ClientMessage.PING:
        await manager.send_to_player(player_id, protocol.make_message(protocol.ServerMessage.PONG))
        return

    if msg_type == protocol.ClientMessage.CREATE:
        await _create(player_id, manager, rooms, tokens, message)
        return

    if msg_type == protocol.ClientMessage.JOIN:
        await _join(player_id, manager, rooms, bus, tokens, message)
        return

    if msg_type == protocol.ClientMessage.LEAVE:
        await _leave(player_id, manager, rooms, bus)
        return

    if msg_type == protocol.ClientMessage.CHAT:
        await _chat(player_id, manager, rooms, bus, message)
        return

    if msg_type == protocol.ClientMessage.START_GAME:
        await _start_game(player_id, manager, rooms, bus, message)
        return

    if msg_type == protocol.ClientMessage.SUBMIT_PLAN:
        await _submit_plan(player_id, manager, rooms, bus, message)
        return

    if msg_type == protocol.ClientMessage.ADD_BOT:
        await _add_bot(player_id, manager, rooms, bus)
        return

    await manager.send_to_player(
        player_id,
        protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message=f"Неизвестный тип сообщения: {msg_type!r}",
        ),
    )


async def _create(player_id, manager, rooms, tokens, message: dict) -> None:
    if manager.room_of(player_id) is not None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.ALREADY_IN_ROOM,
            message="Вы уже находитесь в комнате",
        ))
        return

    max_players = protocol.parse_max_players(message)
    if max_players is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message=f"max_players должно быть от {MIN_PLAYERS} до {MAX_PLAYERS}",
        ))
        return

    room = rooms.create(host_id=player_id, host_name=protocol.parse_player_name(message), max_players=max_players)
    manager.set_room(player_id, room.code)

    token = await tokens.issue(player_id)

    await manager.send_to_player(player_id, protocol.make_message(
        protocol.ServerMessage.CREATED,
        room_code=room.code,
        player_id=player_id,
        token=token,
        host_id=room.host_id,
        max_players=room.max_players,
        status=room.status.value,
        players=_players_payload(room),
    ))


async def _join(player_id, manager, rooms, bus, tokens, message: dict) -> None:
    if manager.room_of(player_id) is not None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.ALREADY_IN_ROOM,
            message="Вы уже находитесь в комнате",
        ))
        return

    code = protocol.parse_room_code(message)
    room = rooms.get(code)
    if room is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.ROOM_NOT_FOUND,
            message="Комната не найдена",
        ))
        return

    if room.status is not RoomStatus.WAITING:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Комната уже не ждёт игроков",
        ))
        return

    if room.is_full:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.ROOM_FULL,
            message="Комната заполнена",
        ))
        return

    player = Player(id=player_id, name=protocol.parse_player_name(message))
    room.add_player(player)
    manager.set_room(player_id, code)

    token = await tokens.issue(player_id)

    await manager.send_to_player(player_id, protocol.make_message(
        protocol.ServerMessage.JOINED,
        room_code=code,
        player_id=player_id,
        token=token,
        host_id=room.host_id,
        max_players=room.max_players,
        status=room.status.value,
        players=_players_payload(room),
    ))

    await bus.publish(code, protocol.make_message(
        protocol.ServerMessage.PLAYER_JOINED,
        player_id=player_id,
        player_name=player.name,
        is_bot=False,
    ))


async def _leave(player_id, manager, rooms, bus) -> None:
    code = manager.room_of(player_id)
    if code is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.NOT_IN_ROOM,
            message="Вы не находитесь в комнате",
        ))
        return

    room = rooms.get(code)
    if room is not None:
        leave_room(room, player_id)
    manager.clear_room(player_id)

    await manager.send_to_player(player_id, protocol.make_message(protocol.ServerMessage.LEFT))

    await bus.publish(code, protocol.make_message(
        protocol.ServerMessage.PLAYER_LEFT,
        player_id=player_id,
    ))

    if room is not None and room.is_empty:
        rooms.remove(code)


async def _chat(player_id, manager, rooms, bus, message: dict) -> None:
    code = manager.room_of(player_id)
    if code is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.NOT_IN_ROOM,
            message="Вы не находитесь в комнате",
        ))
        return

    room = rooms.get(code)
    player = room.players.get(player_id) if room else None
    await bus.publish(code, protocol.make_message(
        protocol.ServerMessage.CHAT,
        player_id=player_id,
        player_name=player.name if player else "?",
        text=protocol.parse_text(message),
    ))


async def _handle_disconnect(player_id, manager, rooms, bus) -> None:
    code = manager.room_of(player_id)
    if code is not None:
        room = rooms.get(code)
        if room is not None and disconnect_player(room, player_id):
            await bus.publish(code, protocol.make_message(
                protocol.ServerMessage.PLAYER_DISCONNECTED,
                player_id=player_id,
            ))
    manager.disconnect_ws(player_id)




def _players_payload(room: Room) -> list[dict]:
    return [{"id": p.id, "name": p.name, "is_host": p.is_host, "is_bot": p.is_bot} for p in room.players.values()]


def _resync_message(room: Room, player_id: str) -> dict:
    """Текущее состояние стола для переподключившегося игрока."""
    payload = {
        "room_code": room.code,
        "player_id": player_id,
        "host_id": room.host_id,
        "max_players": room.max_players,
        "status": room.status.value,
        "players": _players_payload(room),
    }
    if room.game_state is not None:
        payload["state"] = public_state(room.game_state)
        payload["planning_timeout"] = get_settings().planning_timeout_seconds
        if room.game_state.phase is Phase.PLANNING and room.planning_deadline is not None:
            payload["planning_deadline"] = room.planning_deadline
    return protocol.make_message(protocol.ServerMessage.RESYNC, **payload)


async def _start_game(player_id, manager, rooms, bus, message: dict) -> None:
    code = manager.room_of(player_id)
    room = rooms.get(code) if code else None
    if room is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.NOT_IN_ROOM,
            message="Вы не в комнате",
        ))
        return
    if player_id != room.host_id:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Начать игру может только хост",
        ))
        return
    if room.status is not RoomStatus.WAITING:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Игра уже идёт",
        ))
        return
    if not room.can_start:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Недостаточно игроков (минимум 3)",
        ))
        return

    start_game(room)

    planning_timeout = get_settings().planning_timeout_seconds
    room.planning_deadline = time.time() + planning_timeout
    await bus.publish(code, protocol.make_message(
        protocol.ServerMessage.GAME_STARTED,
        room_code=code,
        players=_players_payload(room),
        state=public_state(room.game_state),
        planning_timeout=planning_timeout,
        planning_deadline=room.planning_deadline,
    ))

    task = asyncio.create_task(_game_loop(room, bus, code))
    _game_tasks.add(task)
    task.add_done_callback(_game_tasks.discard)


async def _submit_plan(player_id, manager, rooms, bus, message: dict) -> None:
    code = manager.room_of(player_id)
    room = rooms.get(code) if code else None
    state = room.game_state if room else None
    if room is None or state is None or room.status is not RoomStatus.PLAYING:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.NOT_IN_ROOM,
            message="Игра не идёт",
        ))
        return

    actions = protocol.parse_actions(message)
    if actions is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="actions: список из 3 разных карт",
        ))
        return

    try:
        submit_plan(state, player_id, actions)
    except ValueError as exc:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message=str(exc),
        ))
        return

    await manager.send_to_player(player_id, protocol.make_message(
        protocol.ServerMessage.PLAN_SUBMITTED, player_id=player_id))


async def _add_bot(player_id, manager, rooms, bus) -> None:
    code = manager.room_of(player_id)
    room = rooms.get(code) if code else None
    if room is None:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.NOT_IN_ROOM,
            message="Вы не в комнате",
        ))
        return
    if player_id != room.host_id:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Добавлять ботов может только хост",
        ))
        return
    if room.status is not RoomStatus.WAITING:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.BAD_MESSAGE,
            message="Комната уже не ждёт игроков",
        ))
        return
    if room.is_full:
        await manager.send_to_player(player_id, protocol.make_message(
            protocol.ServerMessage.ERROR,
            code=protocol.ErrorCode.ROOM_FULL,
            message="Комната заполнена",
        ))
        return

    bot = room.add_bot()
    await bus.publish(code, protocol.make_message(
        protocol.ServerMessage.PLAYER_JOINED,
        player_id=bot.id,
        player_name=bot.name,
        is_bot=True,
    ))


async def _game_loop(room, bus, code) -> None:
    """Фоновая задача: полный цикл партии (планирование -> ограбление -> ...)."""

    async def on_event(event) -> None:
        await bus.publish(code, _event_payload(event))

    try:
        await run_game(room, on_event, get_settings().planning_timeout_seconds, step_delay=get_settings().step_delay_seconds)
    except Exception:
        logger.exception("Ошибка игрового цикла комнаты %s", code)


def _event_payload(event) -> dict:
    """Преобразует GameEvent в серверное сообщение для трансляции."""
    return {"type": event.type, "round_number": event.round_number, **event.data}
