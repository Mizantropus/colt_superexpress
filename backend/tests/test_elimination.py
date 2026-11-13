"""Тесты выбывания."""

import random

from app.game.elimination import (
    eliminate_all_off_train,
    eliminate_bandit,
    eliminate_in_car,
    resolve_off_train,
)
from app.game.models import Action, Direction, Level, Position
from app.game.planning import submit_plan
from app.game.setup import setup_game


def _state(n: int = 3):
    players = [(f"p{i}", f"Игрок {i}") for i in range(n)]
    return setup_game(players, first_player_id="p0", rng=random.Random(0))


def _bandit_at(state, pid, car_index, level=Level.INSIDE, lane=0,
               direction=Direction.TOWARD_LOCOMOTIVE):
    b = state.bandit_by_id(pid)
    b.position = Position(car_index=car_index, level=level, lane=lane)
    b.direction = direction
    return b


def test_eliminate_bandit() -> None:
    state = _state(3)
    state.bandit_by_id("p0").off_train = True
    events = eliminate_bandit(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.eliminated is True
    assert b.off_train is False
    assert events[0].type == "eliminated"


def test_eliminate_bandit_idempotent() -> None:
    state = _state(3)
    eliminate_bandit(state, "p0")
    assert eliminate_bandit(state, "p0") == []


def test_resolve_off_train_saved_by_horse() -> None:
    state = _state(3)
    submit_plan(state, "p0", [Action.HORSE, Action.MOVE, Action.SHOOT])
    state.played_counts["p0"] = 0  # current_action = HORSE
    state.bandit_by_id("p0").off_train = True
    saved, events = resolve_off_train(state, "p0")
    assert saved is True
    assert events == []
    assert state.bandit_by_id("p0").eliminated is False
    assert state.bandit_by_id("p0").off_train is True  # лошадь применит движок


def test_resolve_off_train_eliminates() -> None:
    state = _state(3)
    submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, Action.HORSE])
    state.played_counts["p0"] = 0  # current_action = MOVE (не лошадь)
    state.bandit_by_id("p0").off_train = True
    saved, events = resolve_off_train(state, "p0")
    assert saved is False
    assert events and events[0].type == "eliminated"
    assert state.bandit_by_id("p0").eliminated is True
    assert state.bandit_by_id("p0").off_train is False


def test_eliminate_in_car() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    _bandit_at(state, "p1", car_index=3, level=Level.ROOF)
    _bandit_at(state, "p2", car_index=4)
    events = eliminate_in_car(state, 3)
    assert state.bandit_by_id("p0").eliminated is True
    assert state.bandit_by_id("p1").eliminated is True
    assert state.bandit_by_id("p2").eliminated is False
    assert len(events) == 2


def test_eliminate_in_car_skips_off_train() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    _bandit_at(state, "p1", car_index=3)
    state.bandit_by_id("p1").off_train = True
    eliminate_in_car(state, 3)
    assert state.bandit_by_id("p0").eliminated is True
    assert state.bandit_by_id("p1").eliminated is False  # вне вагона


def test_eliminate_all_off_train() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    _bandit_at(state, "p1", car_index=4)
    state.bandit_by_id("p0").off_train = True
    events = eliminate_all_off_train(state)
    assert state.bandit_by_id("p0").eliminated is True
    assert state.bandit_by_id("p1").eliminated is False
    assert len(events) == 1