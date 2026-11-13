"""Инициализация партии: раскладка поезда и расстановка бандитов."""

from __future__ import annotations

import random

from app.game.models import (
    WAGON_VALUES,
    Bandit,
    Direction,
    Level,
    Position,
    TrainCar,
    TrainCarKind,
)
from app.game.state import GameState, Phase

MIN_PLAYERS = 3
MAX_PLAYERS = 7


def build_train(num_players: int, rng: random.Random | None = None) -> list[TrainCar]:
    """Строит поезд: Делориан + локомотив + (num_players + 1) вагонов.

    Номиналы $ (11..18) перемешиваются, поэтому суммы на вагонах случайны.
    """
    rng = rng or random.Random()
    if not (MIN_PLAYERS <= num_players <= MAX_PLAYERS):
        raise ValueError(f"Число игроков должно быть от {MIN_PLAYERS} до {MAX_PLAYERS}")

    wagon_values = list(WAGON_VALUES)
    rng.shuffle(wagon_values)

    cars: list[TrainCar] = [
        TrainCar(kind=TrainCarKind.DELOREAN),
        TrainCar(kind=TrainCarKind.LOCOMOTIVE),
    ]
    wagon_count = num_players + 1
    cars += [
        TrainCar(kind=TrainCarKind.WAGON, value=wagon_values[i])
        for i in range(wagon_count)
    ]
    return cars


def setup_game(
    players: list[tuple[str, str]],
    *,
    first_player_id: str | None = None,
    rng: random.Random | None = None,
) -> GameState:
    """Инициализирует партию.

    players — список (player_id, name) в порядке посадки (круговой стол).

    Расстановка (по правилам):
    - первый игрок — в предпоследний вагон, далее к локомотиву, последний
      игрок — в первый вагон (ближайший к локомотиву);
    - половина бандитов, ближняя к хвосту, смотрит на локомотив, другая
      половина — на хвост; при нечётном числе центральный — на локомотив.
    """
    rng = rng or random.Random()
    num_players = len(players)
    train = build_train(num_players, rng)

    player_ids = [pid for pid, _ in players]
    if first_player_id is None:
        first_player_id = rng.choice(player_ids)
    elif first_player_id not in player_ids:
        raise ValueError("first_player_id не найден среди игроков")

    name_by_id = {pid: name for pid, name in players}

    # Порядок хода: от первого игрока по кругу.
    start = player_ids.index(first_player_id)
    turn_order_ids = player_ids[start:] + player_ids[:start]

    # Вагон каждого игрока (по порядку хода):
    # первый игрок — предпоследний вагон, последний — ближайший к локомотиву.
    # Вагон k (от локомотива) имеет car_index = k + 1 (0 — Делориан, 1 — локомотив).
    car_index_by_id: dict[str, int] = {}
    for j, pid in enumerate(turn_order_ids):
        car_index_by_id[pid] = num_players - j + 1

    # Взгляды: от локомотива к хвосту первая половина — на хвост, остальные — на локомотив.
    direction_by_id: dict[str, Direction] = {}
    loc_order = list(reversed(turn_order_ids))
    for idx, pid in enumerate(loc_order):
        direction_by_id[pid] = (
            Direction.TOWARD_TAIL if idx < num_players // 2 else Direction.TOWARD_LOCOMOTIVE
        )

    # Бандиты хранятся в порядке посадки; край вагона — REAR (на старте каждый в своём вагоне).
    bandits = [
        Bandit(
            player_id=pid,
            name=name_by_id[pid],
            position=Position(
                car_index=car_index_by_id[pid],
                level=Level.INSIDE,
                lane=0,
            ),
            direction=direction_by_id[pid],
        )
        for pid in player_ids
    ]

    return GameState(
        train=train,
        bandits=bandits,
        phase=Phase.PLANNING,
        round_number=1,
        first_player_id=first_player_id,
    )