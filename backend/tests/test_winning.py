"""Тесты условий победы."""

from app.game.models import (
    Bandit,
    Direction,
    Level,
    Position,
    TrainCar,
    TrainCarKind,
)
from app.game.state import GameState
from app.game.winning import check_winner


def _state(active_count: int, wagon_count: int) -> GameState:
    train = [TrainCar(kind=TrainCarKind.DELOREAN), TrainCar(kind=TrainCarKind.LOCOMOTIVE)]
    train += [TrainCar(kind=TrainCarKind.WAGON, value=11 + i) for i in range(wagon_count)]
    bandits = [
        Bandit(f"p{i}", f"P{i}", Position(car_index=2, level=Level.INSIDE, lane=0), Direction.TOWARD_TAIL)
        for i in range(active_count)
    ]
    return GameState(train=train, bandits=bandits)


def test_one_bandit_wins() -> None:
    state = _state(active_count=1, wagon_count=3)
    finished, winner = check_winner(state)
    assert finished is True
    assert winner == "p0"


def test_no_wagons_richest_wins() -> None:
    state = _state(active_count=3, wagon_count=0)
    state.bandit_by_id("p0").money = 5
    state.bandit_by_id("p1").money = 20
    state.bandit_by_id("p2").money = 10
    finished, winner = check_winner(state)
    assert finished is True
    assert winner == "p1"


def test_all_eliminated_draw() -> None:
    state = _state(active_count=3, wagon_count=3)
    for b in state.bandits:
        b.eliminated = True
    finished, winner = check_winner(state)
    assert finished is True
    assert winner is None


def test_game_continues() -> None:
    state = _state(active_count=3, wagon_count=3)
    finished, winner = check_winner(state)
    assert finished is False
    assert winner is None

def test_tie_roof_beats_inside() -> None:
    state = _state(active_count=2, wagon_count=0)
    state.bandit_by_id("p0").position = Position(car_index=1, level=Level.INSIDE, lane=0)
    state.bandit_by_id("p1").position = Position(car_index=1, level=Level.ROOF, lane=0)
    state.bandit_by_id("p0").money = 10
    state.bandit_by_id("p1").money = 10
    finished, winner = check_winner(state)
    assert finished is True
    assert winner == "p1"  # на крыше


def test_tie_roof_closer_to_tail() -> None:
    state = _state(active_count=2, wagon_count=0)
    state.bandit_by_id("p0").position = Position(car_index=1, level=Level.ROOF, lane=1)
    state.bandit_by_id("p1").position = Position(car_index=1, level=Level.ROOF, lane=0)
    state.bandit_by_id("p0").money = 10
    state.bandit_by_id("p1").money = 10
    finished, winner = check_winner(state)
    assert finished is True
    assert winner == "p1"  # REAR — ближе к хвосту
