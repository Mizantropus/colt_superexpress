"""Выбывание бандитов."""

from __future__ import annotations

from app.game.models import Action
from app.game.planning import current_action
from app.game.state import GameEvent, GameState


def eliminate_bandit(state: GameState, player_id: str) -> list[GameEvent]:
    """Помечает бандита выбывшим (снимает и off_train)."""
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated:
        return []
    bandit.eliminated = True
    bandit.off_train = False
    return [state.record_event("eliminated", player_id=player_id)]


def resolve_off_train(state: GameState, player_id: str) -> tuple[bool, list[GameEvent]]:
    """Разрешает бандита, вытолкнутого за пределы поезда.

    Вызывается движком в ход бандита. Возвращает (спасён_лошадью, события):
    - (True, []) — спасён лошадью (движок должен применить apply_horse);
    - (False, [eliminated...]) — выбыл (события здесь).
    """
    bandit = state.bandit_by_id(player_id)
    if bandit is None or not bandit.off_train:
        return False, []

    if current_action(state, player_id) is Action.HORSE:
        return True, []

    return False, eliminate_bandit(state, player_id)


def eliminate_in_car(state: GameState, car_index: int) -> list[GameEvent]:
    """Выбывают все бандиты внутри/на крыше указанного вагона (отцепление)."""
    events: list[GameEvent] = []
    for bandit in state.active_bandits():
        if bandit.off_train:
            continue
        if bandit.position.car_index == car_index:
            events.extend(eliminate_bandit(state, bandit.player_id))
    return events


def eliminate_all_off_train(state: GameState) -> list[GameEvent]:
    """Выбывают бандиты, оставшиеся за поездом (выбитые после последнего хода)."""
    events: list[GameEvent] = []
    for bandit in state.active_bandits():
        if bandit.off_train:
            events.extend(eliminate_bandit(state, bandit.player_id))
    return events