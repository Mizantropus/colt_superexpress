"""Тесты игрового движка."""

import random

from app.game.engine import resolve_round
from app.game.models import Action, Direction, Level, LOCOMOTIVE_INDEX, Position, Posture
from app.game.planning import start_robbery, submit_plan
from app.game.setup import setup_game
from app.game.state import Phase

# Три разных безвредных действия (без выстрелов и движения за поезд).
HARMLESS = [Action.TURN_AROUND, Action.CHANGE_LEVEL, Action.HIP_FIRE]


def _state(n: int = 3):
    players = [(f"p{i}", f"Игрок {i}") for i in range(n)]
    return setup_game(players, first_player_id="p0", rng=random.Random(0))


def test_resolve_round_full() -> None:
    state = _state(3)
    for pid in ("p0", "p1", "p2"):
        submit_plan(state, pid, list(HARMLESS))
    start_robbery(state)
    events = resolve_round(state)
    assert state.phase is Phase.PLANNING  # новый раунд
    assert state.round_number == 2
    assert "wagon_detached" in [e.type for e in events]
    assert sum(1 for e in events if e.type == "turned_around") == 3


def test_prone_bandit_loses_action() -> None:
    state = _state(3)
    submit_plan(state, "p0", [Action.MOVE, Action.TURN_AROUND, Action.CHANGE_LEVEL])
    submit_plan(state, "p1", list(HARMLESS))
    submit_plan(state, "p2", list(HARMLESS))
    start_robbery(state)
    state.bandit_by_id("p0").posture = Posture.PRONE
    events = resolve_round(state)
    assert "stood_up" in [e.type for e in events]
    assert not any(e.type == "moved" and e.data["player_id"] == "p0" for e in events)


def test_off_train_saved_by_horse() -> None:
    state = _state(3)
    submit_plan(state, "p0", [Action.HORSE, Action.TURN_AROUND, Action.HIP_FIRE])
    submit_plan(state, "p1", list(HARMLESS))
    submit_plan(state, "p2", list(HARMLESS))
    start_robbery(state)
    state.bandit_by_id("p0").off_train = True
    events = resolve_round(state)
    p0 = state.bandit_by_id("p0")
    assert p0.off_train is False
    assert p0.position.car_index == LOCOMOTIVE_INDEX
    assert p0.position.level is Level.ROOF
    assert "horse" in [e.type for e in events]


def test_delorean_rewind_replays_actions() -> None:
    state = _state(3)
    p0 = state.bandit_by_id("p0")
    p0.position = Position(car_index=1, level=Level.INSIDE, lane=0)
    p0.direction = Direction.TOWARD_LOCOMOTIVE
    submit_plan(state, "p0", [Action.MOVE, Action.TURN_AROUND, Action.CHANGE_LEVEL])
    submit_plan(state, "p1", list(HARMLESS))
    submit_plan(state, "p2", list(HARMLESS))
    start_robbery(state)
    events = resolve_round(state)
    assert "delorean_entered" in [e.type for e in events]
    # первый MOVE ушёл в Делориан; повторный MOVE после перемотки — ровно один "moved"
    assert sum(1 for e in events if e.type == "moved" and e.data["player_id"] == "p0") == 1