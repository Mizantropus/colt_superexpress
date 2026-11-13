"""Тесты «Делориана» (Машины времени)."""

import random

from app.game.delorean import apply_delorean_entry
from app.game.models import Action, Direction, Level
from app.game.planning import start_robbery, submit_plan
from app.game.setup import setup_game


def _state(n: int = 3):
    players = [(f"p{i}", f"Игрок {i}") for i in range(n)]
    return setup_game(players, first_player_id="p0", rng=random.Random(0))


def test_delorean_teleports_to_tail() -> None:
    state = _state(3)
    last = state.last_wagon_index
    events = apply_delorean_entry(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.car_index == last
    assert b.position.level is Level.INSIDE
    assert b.direction is Direction.TOWARD_LOCOMOTIVE
    assert "delorean_entered" in [e.type for e in events]


def test_delorean_rewinds_played_cards() -> None:
    state = _state(3)
    submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, Action.HORSE])
    start_robbery(state)
    state.played_counts["p0"] = 2  # сыграл 2 карты
    apply_delorean_entry(state, "p0")
    assert state.played_counts["p0"] == 0  # перемотка


def test_delorean_paradox_eliminates() -> None:
    state = _state(3)
    apply_delorean_entry(state, "p0")  # первый вход
    events = apply_delorean_entry(state, "p0")  # второй вход — парадокс
    assert state.bandit_by_id("p0").eliminated is True
    assert "time_paradox" in [e.type for e in events]
    assert "eliminated" in [e.type for e in events]