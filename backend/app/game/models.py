"""Доменная модель игры «Кольт Суперэкспресс».

Здесь — только перечисления и базовые типы данных, без игровой логики.
Понятия (по договорённости):
- Действия (Action): 6 карт действий.
- Состояния (Posture, Direction): поза и направление взгляда.
- Координаты (car_index + level): в каком вагоне и на каком уровне.
- Порядок на уровне (lane): положение относительно других бандитов
  в том же вагоне и на том же уровне.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


# --- Действия ---------------------------------------------------------------

class Action(str, Enum):
    """Шесть базовых действий (карты)."""

    MOVE = "move"                    # Переместиться
    CHANGE_LEVEL = "change_level"    # Сменить уровень
    TURN_AROUND = "turn_around"      # Развернуться
    SHOOT = "shoot"                  # Выстрел
    HORSE = "horse"                  # Лошадь
    HIP_FIRE = "hip_fire"            # Выстрел от бедра


# --- Состояния --------------------------------------------------------------

class Level(str, Enum):
    """Уровень (вертикальная координата)."""

    INSIDE = "inside"   # внутри (внизу)
    ROOF = "roof"       # на крыше


class Direction(str, Enum):
    """Направление взгляда вдоль поезда.

    Семантическое направление; визуальное «влево/вправо» задаётся при
    отрисовке (когда зафиксируем сторону движения поезда).
    """

    TOWARD_LOCOMOTIVE = "toward_locomotive"  # к голове поезда
    TOWARD_TAIL = "toward_tail"              # к хвосту поезда

    def opposite(self) -> "Direction":
        if self is Direction.TOWARD_LOCOMOTIVE:
            return Direction.TOWARD_TAIL
        return Direction.TOWARD_LOCOMOTIVE


class Posture(str, Enum):
    """Поза бандита."""

    STANDING = "standing"
    PRONE = "prone"   # лежит навзничь


# --- Поезд ------------------------------------------------------------------

class TrainCarKind(str, Enum):
    DELOREAN = "delorean"
    LOCOMOTIVE = "locomotive"
    WAGON = "wagon"


# Номиналы вагонов: 8 вагонов с уникальными суммами $11..$18
WAGON_VALUES: tuple[int, ...] = tuple(range(11, 19))

# Индексы в списке поезда (от головы к хвосту)
DELOREAN_INDEX = 0
LOCOMOTIVE_INDEX = 1
FIRST_WAGON_INDEX = 2   # первый вагон сразу за локомотивом


@dataclass(frozen=True)
class TrainCar:
    """Один элемент поезда (Делориан, локомотив или вагон)."""

    kind: TrainCarKind
    value: int | None = None   # номинал $ — только для вагонов


@dataclass(frozen=True)
class Position:
    """Позиция бандита: вагон + уровень + lane (порядок слева направо на уровне).

    lane = 0 — ближе к хвосту (левее), больше — ближе к локомотиву (правее).
    """

    car_index: int
    level: Level
    lane: int = 0


@dataclass
class Bandit:
    """Бандит: идентичность, координаты и состояние."""

    player_id: str
    name: str
    position: Position
    direction: Direction
    posture: Posture = Posture.STANDING
    eliminated: bool = False
    off_train: bool = False
    money: int = 0

    @property
    def is_prone(self) -> bool:
        return self.posture is Posture.PRONE


def assign_lane(cell_bandits: list[Bandit], from_tail: bool) -> tuple[int, list[tuple[str, int]]]:
    """Назначает lane входящему бандиту и сдвигает уже стоящих в ячейке.

    cell_bandits — бандиты, уже находящиеся в (вагон, уровень).
    from_tail=True — вход со стороны хвоста: новый становится левее всех (lane=0),
    остальные сдвигаются на +1. Иначе новый становится правее всех.

    Возвращает (lane, shifted), где shifted — [(player_id, новый lane), ...]
    для сдвинутых бандитов (клиенты применяют их новое положение).
    """
    shifted: list[tuple[str, int]] = []
    if from_tail:
        for b in cell_bandits:
            b.position = replace(b.position, lane=b.position.lane + 1)
            shifted.append((b.player_id, b.position.lane))
        return 0, shifted
    max_lane = max((b.position.lane for b in cell_bandits), default=-1)
    return max_lane + 1, shifted