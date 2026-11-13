"""Конец раунда: отцепление вагона, присуждение $, смена первого игрока."""

from __future__ import annotations

from app.game.elimination import eliminate_all_off_train, eliminate_in_car
from app.game.models import Level
from app.game.planning import start_planning
from app.game.state import GameEvent, GameState, Phase
from app.game.winning import check_winner


def end_round(state: GameState) -> list[GameEvent]:
    """Завершает раунд: отцепляет хвостовой вагон, присуждает $, начинает новый раунд.

    Проверка победы добавляется в пункте 18 (перед началом нового раунда).
    """
    events: list[GameEvent] = []

    # 0. Выбитые за поезд и не спасённые лошадью выбывают.
    events.extend(eliminate_all_off_train(state))

    detached_index = state.last_wagon_index
    detached_car = state.train[detached_index]
    value = detached_car.value or 0

    # 1. Бандиты в отцепленном вагоне выбывают.
    events.extend(eliminate_in_car(state, detached_index))

    # 2. $ достаётся ближайшему к отцепленному вагону бандиту.
    closest = _closest_to_detached(state)
    if closest is not None:
        closest.money += value
        events.append(state.record_event(
            "money_awarded",
            player_id=closest.player_id,
            amount=value,
        ))

    # 3. Отцепляем вагон.
    state.train.pop()
    events.append(state.record_event(
        "wagon_detached",
        car_index=detached_index,
        value=value,
    ))

    # 4. Проверка победы.
    finished, winner_id = check_winner(state)
    if finished:
        state.phase = Phase.FINISHED
        state.winner_id = winner_id
        events.append(state.record_event("game_finished", winner_id=winner_id))

    return events


def begin_next_round(state: GameState) -> GameEvent:
    """Начинает следующий раунд: смена первого игрока и фаза планирования."""
    state.round_number += 1
    state.first_player_id = state.next_player_id(state.first_player_id)
    start_planning(state)
    return state.record_event("round_started", first_player_id=state.first_player_id)


def _closest_to_detached(state: GameState):
    """Бандит, ближайший к отцепленному вагону (крыша приоритетна)."""
    candidates = [b for b in state.active_bandits() if not b.off_train]
    if not candidates:
        return None

    order_by_id = {b.player_id: i for i, b in enumerate(state.bandits)}

    def sort_key(b):
        return (
            -b.position.car_index,                       # ближе к хвосту
            0 if b.position.level is Level.ROOF else 1,  # крыша приоритетна
            b.position.lane,                             # меньше lane — ближе к хвосту
            order_by_id[b.player_id],
        )

    return min(candidates, key=sort_key)