"""Колода действий и фаза планирования."""

from __future__ import annotations

from app.game.models import Action
from app.game.state import GameState, Phase

# Рука: по одной карте каждого из 6 действий (у всех игроков одинаковая).
HAND_SIZE = 6
PLAN_SIZE = 3
FULL_HAND: tuple[Action, ...] = tuple(Action)


def start_planning(state: GameState) -> None:
    """Начинает фазу планирования: очищает планы и сбрасывает прогресс хода."""
    state.plans.clear()
    state.played_counts.clear()
    state.delorean_entered.clear()
    state.phase = Phase.PLANNING
    state.current_player_id = None


def submit_plan(state: GameState, player_id: str, actions: list[Action]) -> None:
    """Принимает тайную стопку из 3 карт (верхняя — 1-е действие)."""
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated:
        raise ValueError("Игрок не участвует в партии")

    if state.phase is not Phase.PLANNING:
        raise ValueError("Сейчас не фаза планирования")

    if len(actions) != PLAN_SIZE:
        raise ValueError(f"Нужно выбрать ровно {PLAN_SIZE} карты")

    if not all(isinstance(a, Action) for a in actions):
        raise ValueError("Неизвестное действие")

    if len(set(actions)) != PLAN_SIZE:
        raise ValueError("Карты в стопке не должны повторяться")

    state.plans[player_id] = list(actions)


def all_plans_submitted(state: GameState) -> bool:
    """Все ли активные игроки отправили свои стопки."""
    active_ids = {b.player_id for b in state.active_bandits()}
    return active_ids <= set(state.plans)


def current_action(state: GameState, player_id: str) -> Action | None:
    """Действие игрока на текущем шаге ограбления (или None)."""
    plan = state.plans.get(player_id)
    if plan is None:
        return None
    idx = state.played_counts.get(player_id, 0)
    if idx >= len(plan):
        return None
    return plan[idx]


def start_robbery(state: GameState) -> None:
    """Переходит к фазе ограбления: первый шаг, ходит первый игрок."""
    state.phase = Phase.ROBBERY
    state.played_counts = {b.player_id: 0 for b in state.active_bandits()}
    state.current_player_id = state.next_player_id(None)