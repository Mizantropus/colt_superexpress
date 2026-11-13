"""Игровой движок: оркестрация фазы ограбления."""

from __future__ import annotations

from app.game.actions import (
    apply_change_level,
    apply_hip_fire,
    apply_horse,
    apply_move,
    apply_shoot,
    apply_turn_around,
)
from app.game.elimination import resolve_off_train
from app.game.models import Action, Posture
from app.game.planning import current_action
from app.game.round_end import end_round
from app.game.state import GameEvent, GameState, Phase
from app.game.winning import check_winner


def resolve_round(state: GameState) -> list[GameEvent]:
    """Разрешает фазу ограбления: все действия, затем конец раунда.

    Предполагает, что планирование завершено и start_robbery() уже вызван.
    Возвращает список событий для трансляции и анимаций.
    """
    events: list[GameEvent] = []

    while True:
        progressed = False
        for bandit in state.turn_order():
            if bandit.eliminated:
                continue
            turn_events = _resolve_turn(state, bandit.player_id)
            if not turn_events:
                continue
            events.extend(turn_events)
            progressed = True

            # Победа (остался один / все выбыли) — завершаем сразу.
            finished, winner_id = check_winner(state)
            if finished:
                state.phase = Phase.FINISHED
                state.winner_id = winner_id
                events.append(state.record_event("game_finished", winner_id=winner_id))
                return events

        if not progressed:
            break

    # Все карты сыграны — конец раунда (отцепление вагона и т.д.).
    events.extend(end_round(state))
    return events


def _resolve_turn(state: GameState, player_id: str) -> list[GameEvent]:
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated:
        return []

    events: list[GameEvent] = []

    # Вытолкнут за поезд: лошадь спасает, иначе выбывает.
    if bandit.off_train:
        saved, ev = resolve_off_train(state, player_id)
        events.extend(ev)
        if saved:
            state.played_counts[player_id] += 1
            events.extend(apply_horse(state, player_id))
        return events

    # Следующая карта.
    action = current_action(state, player_id)
    if action is None:
        return events

    # Сигнал о разыгрываемой карте (для анимации раскрытия + прокрутки поезда).
    events.append(state.record_event("action_started", player_id=player_id, action=action.value))

    state.played_counts[player_id] += 1

    # Лежит навзничь: теряет действие (встаёт), кроме «Выстрела от бедра».
    if bandit.is_prone:
        if action is Action.HIP_FIRE:
            events.extend(apply_hip_fire(state, player_id))
        else:
            bandit.posture = Posture.STANDING
            events.append(state.record_event("stood_up", player_id=player_id))
        return events

    # Обычное действие.
    events.extend(_apply_action(state, player_id, action))
    return events


def _apply_action(state: GameState, player_id: str, action: Action) -> list[GameEvent]:
    if action is Action.MOVE:
        return apply_move(state, player_id)
    if action is Action.CHANGE_LEVEL:
        return apply_change_level(state, player_id)
    if action is Action.TURN_AROUND:
        return apply_turn_around(state, player_id)
    if action is Action.SHOOT:
        return apply_shoot(state, player_id)
    if action is Action.HORSE:
        return apply_horse(state, player_id)
    if action is Action.HIP_FIRE:
        return apply_hip_fire(state, player_id)
    return []