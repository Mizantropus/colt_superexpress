"""Комнаты (лобби): код, хост, статус, слоты, конфиг."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from enum import Enum

from app.game.setup import MAX_PLAYERS, MIN_PLAYERS
from app.game.state import GameState

ROOM_CODE_LENGTH = 6
# Без похожих символов 0/O и 1/I.
_ALPHABET = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "O0I1")

# Имена ботов (выбираются случайно, без повторов в рамках комнаты).
BOT_NAMES = ["Доцент", "Косой", "Хмырь", "Трус", "Балбес", "Бывалый", "Лёлик", "Геша", "Милославский"]


class RoomStatus(str, Enum):
    WAITING = "waiting"    # лобби: набор игроков
    PLAYING = "playing"    # идёт партия
    FINISHED = "finished"  # партия завершена


def generate_room_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


@dataclass
class Player:
    id: str
    name: str
    is_host: bool = False
    connected: bool = True
    disconnected_at: float | None = None
    is_bot: bool = False


@dataclass
class Room:
    code: str
    host_id: str
    max_players: int
    status: RoomStatus = RoomStatus.WAITING
    players: dict[str, Player] = field(default_factory=dict)  # в порядке посадки
    game_state: GameState | None = None
    planning_deadline: float | None = None
    # Игроки, закрывшие окошко результата раунда (для старта следующего раунда).
    round_confirmations: set[str] = field(default_factory=set)

    @property
    def is_empty(self) -> bool:
        return not self.players

    @property
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players

    @property
    def can_start(self) -> bool:
        return MIN_PLAYERS <= len(self.players) <= self.max_players

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def remove_player(self, player_id: str) -> Player | None:
        return self.players.pop(player_id, None)

    def ordered_players(self) -> list[Player]:
        return list(self.players.values())

    def add_bot(self, name: str | None = None, bot_id: str | None = None) -> Player:
        """Добавляет ИИ-игрока в свободный слот (имя — случайное из списка, без повторов)."""
        bot_id = bot_id or f"bot_{secrets.token_hex(4)}"
        if name is None:
            used = {p.name for p in self.players.values() if p.is_bot}
            available = [n for n in BOT_NAMES if n not in used]
            name = secrets.choice(available) if available else f"Бот {len(used) + 1}"
        player = Player(id=bot_id, name=name, is_bot=True)
        self.add_player(player)
        return player


class RoomRegistry:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create(self, host_id: str, host_name: str, max_players: int) -> Room:
        if not (MIN_PLAYERS <= max_players <= MAX_PLAYERS):
            raise ValueError(f"Число игроков должно быть от {MIN_PLAYERS} до {MAX_PLAYERS}")
        while True:
            code = generate_room_code()
            if code not in self._rooms:
                room = Room(code=code, host_id=host_id, max_players=max_players)
                room.add_player(Player(id=host_id, name=host_name, is_host=True))
                self._rooms[code] = room
                return room

    def get(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def remove(self, code: str) -> None:
        self._rooms.pop(code, None)