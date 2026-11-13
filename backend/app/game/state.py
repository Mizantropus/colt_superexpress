"""Состояние игры GameState и фазы раунда."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.game.models import FIRST_WAGON_INDEX, Action, Bandit, Level, TrainCar


class Phase(str, Enum):
    """Фаза игры."""

    PLANNING = "planning"   # игроки тайно выбирают 3 карты
    ROBBERY = "robbery"     # вскрытие и выполнение действий
    FINISHED = "finished"   # игра завершена


@dataclass(frozen=True)
class GameEvent:
    """Запись в истории партии (типизация событий — в пункте 20)."""

    type: str
    round_number: int
    data: dict = field(default_factory=dict)


@dataclass
class GameState:
    """Полное состояние партии.

    train хранится от головы к хвосту: [Делориан, локомотив, вагоны...].
    """

    train: list[TrainCar] = field(default_factory=list)
    bandits: list[Bandit] = field(default_factory=list)
    plans: dict[str, list[Action]] = field(default_factory=dict)
    played_counts: dict[str, int] = field(default_factory=dict)
    delorean_entered: set[str] = field(default_factory=set)
    phase: Phase = Phase.PLANNING
    round_number: int = 1
    first_player_id: str | None = None
    current_player_id: str | None = None
    winner_id: str | None = None
    history: list[GameEvent] = field(default_factory=list)

    # --- Поезд ------------------------------------------------------------

    @property
    def wagon_indices(self) -> list[int]:
        """Индексы вагонов (без Делориана и локомотива)."""
        return list(range(FIRST_WAGON_INDEX, len(self.train)))

    @property
    def last_wagon_index(self) -> int:
        """Индекс хвостового вагона (отцепляется в конце раунда)."""
        return len(self.train) - 1

    @property
    def wagon_count(self) -> int:
        return len(self.wagon_indices)

    # --- Бандиты -----------------------------------------------------------

    def active_bandits(self) -> list[Bandit]:
        return [b for b in self.bandits if not b.eliminated]

    def bandit_by_id(self, player_id: str) -> Bandit | None:
        return next((b for b in self.bandits if b.player_id == player_id), None)

    def bandits_in_cell(self, car_index: int, level: Level) -> list[Bandit]:
        """Активные бандиты в (вагон, уровень)."""
        return [
            b for b in self.active_bandits()
            if not b.off_train
            and b.position.car_index == car_index
            and b.position.level is level
        ]

    @property
    def current_bandit(self) -> Bandit | None:
        if self.current_player_id is None:
            return None
        return self.bandit_by_id(self.current_player_id)

    # --- Очередь -----------------------------------------------------------

    def turn_order(self) -> list[Bandit]:
        """Порядок хода в текущем раунде: от первого игрока по часовой стрелке."""
        if self.first_player_id is None:
            return self.active_bandits()
        start = next(
            (i for i, b in enumerate(self.bandits) if b.player_id == self.first_player_id),
            0,
        )
        ordered = self.bandits[start:] + self.bandits[:start]
        return [b for b in ordered if not b.eliminated]

    def next_player_id(self, after_player_id: str | None) -> str | None:
        """ID игрока, который ходит следующим после after_player_id."""
        order = self.turn_order()
        if not order:
            return None
        if after_player_id is None:
            return order[0].player_id
        ids = [b.player_id for b in order]
        if after_player_id not in ids:
            return order[0].player_id
        idx = ids.index(after_player_id)
        return ids[(idx + 1) % len(ids)]

    # --- Прочее ------------------------------------------------------------

    @property
    def is_finished(self) -> bool:
        return self.phase is Phase.FINISHED

    def record_event(self, event_type: str, **data) -> GameEvent:
        event = GameEvent(type=event_type, round_number=self.round_number, data=data)
        self.history.append(event)
        return event