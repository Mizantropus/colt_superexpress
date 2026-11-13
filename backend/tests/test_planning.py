"""Тесты колоды и фазы планирования."""

import random

import pytest

from app.game.models import Action
from app.game.planning import (
    FULL_HAND,
    HAND_SIZE,
    PLAN_SIZE,
    all_plans_submitted,
    current_action,
    start_robbery,
    submit_plan,
)
from app.game.setup import setup_game
from app.game.state import Phase


def _state(num_players: int = 3):
    players = [(f"p{i}", f"Игрок {i}") for i in range(num_players)]
    return setup_game(players, first_player_id="p0", rng=random.Random(0))


def test_full_hand() -> None:
    assert HAND_SIZE == 6
    assert PLAN_SIZE == 3
    assert len(FULL_HAND) == 6
    assert set(FULL_HAND) == set(Action)


def test_submit_plan() -> None:
    state = _state(3)
    plan = [Action.MOVE, Action.SHOOT, Action.HORSE]
    submit_plan(state, "p0", plan)
    assert state.plans["p0"] == plan
    assert current_action(state, "p0") is Action.MOVE


def test_submit_plan_requires_three_distinct() -> None:
    state = _state(3)
    with pytest.raises(ValueError):
        submit_plan(state, "p0", [Action.MOVE, Action.MOVE])
    with pytest.raises(ValueError):
        submit_plan(state, "p0", [Action.MOVE, Action.MOVE, Action.SHOOT])
    with pytest.raises(ValueError):
        submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, Action.HORSE, Action.MOVE])


def test_submit_plan_invalid_action() -> None:
    state = _state(3)
    with pytest.raises(ValueError):
        submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, "move"])


def test_submit_plan_wrong_phase() -> None:
    state = _state(3)
    state.phase = Phase.ROBBERY
    with pytest.raises(ValueError):
        submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, Action.HORSE])


def test_submit_plan_eliminated() -> None:
    state = _state(3)
    state.bandit_by_id("p1").eliminated = True
    with pytest.raises(ValueError):
        submit_plan(state, "p1", [Action.MOVE, Action.SHOOT, Action.HORSE])


def test_all_plans_submitted() -> None:
    state = _state(3)
    plan = [Action.MOVE, Action.SHOOT, Action.HORSE]
    assert not all_plans_submitted(state)
    for pid in ("p0", "p1", "p2"):
        submit_plan(state, pid, plan)
    assert all_plans_submitted(state)


def test_all_plans_submitted_skips_eliminated() -> None:
    state = _state(3)
    state.bandit_by_id("p2").eliminated = True
    plan = [Action.MOVE, Action.SHOOT, Action.HORSE]
    submit_plan(state, "p0", plan)
    submit_plan(state, "p1", plan)
    assert all_plans_submitted(state)


def test_start_robbery() -> None:
    state = _state(3)
    start_robbery(state)
    assert state.phase is Phase.ROBBERY
    assert state.played_counts == {"p0": 0, "p1": 0, "p2": 0}
    assert state.current_player_id == "p0"