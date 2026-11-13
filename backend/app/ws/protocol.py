"""JSON-протокол WebSocket.

Все сообщения имеют вид {"type": "...", ...поля}.

Клиент -> Сервер:
  - ping
  - create {max_players?: int (3..7), player_name?: str}
  - join {room_code: str, player_name?: str}
  - leave
  - chat {text: str}
  - start_game
  - submit_plan {actions: [str, str, str]}  # три разные карты

Сервер -> Клиент:
  - pong
  - created / joined {room_code, player_id, token, host_id, max_players, status, players[]}
  - left, player_joined, player_left, player_disconnected, player_reconnected, reconnected
  - chat {player_id, player_name, text}
  - error {code, message}
  - game_started {room_code, players[]}, plan_submitted {player_id}, planning_timed_out
  - события игры (moved, changed_level, turned_around, shoot, knocked, horse,
    stood_up, lay_down, eliminated, entered_delorean, time_paradox,
    wagon_detached, money_awarded, round_started, game_finished) —
    в формате {type, round_number, ...data}.
"""

from __future__ import annotations

import json
from typing import Any

from app.game.models import Action
from app.game.setup import MAX_PLAYERS, MIN_PLAYERS


class ClientMessage:
    """Сообщения от клиента к серверу."""

    CREATE = "create"
    JOIN = "join"
    LEAVE = "leave"
    PING = "ping"
    CHAT = "chat"
    START_GAME = "start_game"
    SUBMIT_PLAN = "submit_plan"
    ADD_BOT = "add_bot"
    CONFIRM_ROUND = "confirm_round"


class ServerMessage:
    """Сообщения от сервера к клиенту."""

    CREATED = "created"
    JOINED = "joined"
    LEFT = "left"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PONG = "pong"
    CHAT = "chat"
    ERROR = "error"
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_RECONNECTED = "player_reconnected"
    RECONNECTED = "reconnected"
    RESYNC = "resync"
    GAME_STARTED = "game_started"
    PLAN_SUBMITTED = "plan_submitted"
    PLANNING_TIMED_OUT = "planning_timed_out"


class ErrorCode:
    BAD_MESSAGE = "bad_message"
    ROOM_NOT_FOUND = "room_not_found"
    ROOM_FULL = "room_full"
    ALREADY_IN_ROOM = "already_in_room"
    NOT_IN_ROOM = "not_in_room"
    INTERNAL = "internal"


def make_message(message_type: str, **payload: Any) -> dict[str, Any]:
    """Собирает сообщение вида {"type": ..., ...payload}."""
    return {"type": message_type, **payload}


def error_message(code: str, message: str) -> dict[str, str]:
    """Собирает сообщение об ошибке."""
    return make_message(ServerMessage.ERROR, code=code, message=message)


def decode(raw: str) -> dict[str, Any]:
    """Разбирает сырой текст в словарь сообщения."""
    data = json.loads(raw)
    if not isinstance(data, dict) or "type" not in data:
        raise ValueError("Сообщение должно быть объектом с полем 'type'")
    return data


# --- Валидация полей ---------------------------------------------------------

def parse_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_max_players(message: dict) -> int | None:
    """Извлекает и валидирует max_players (3..7)."""
    value = parse_int(message.get("max_players"), None)
    if value is None or not (MIN_PLAYERS <= value <= MAX_PLAYERS):
        return None
    return value


def parse_actions(message: dict) -> list[Action] | None:
    """Извлекает список из 3 карт действий (без проверки повторов — её делает submit_plan)."""
    raw = message.get("actions")
    if not isinstance(raw, list) or len(raw) != 3:
        return None
    try:
        return [Action(str(a)) for a in raw]
    except (ValueError, TypeError):
        return None


def parse_room_code(message: dict) -> str:
    return str(message.get("room_code") or "").strip().upper()


def parse_player_name(message: dict) -> str:
    return str(message.get("player_name") or "").strip() or "Игрок"


def parse_text(message: dict) -> str:
    return str(message.get("text") or "")