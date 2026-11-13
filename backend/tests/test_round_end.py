"""Тесты конца раунда."""

from app.game.models import (
    Bandit,
    Direction,
    Level,
    Position,
    Posture,
    TrainCar,
    TrainCarKind,
)
from app.game.round_end import end_round
from app.game.state import GameState, Phase


def _controlled_state() -> GameState:
    """3 бандита, 4 вагона с известными номиналами $11..14 (car 2..5)."""
    train = [
        TrainCar(kind=TrainCarKind.DELOREAN),
        TrainCar(kind=TrainCarKind.LOCOMOTIVE),
        TrainCar(kind=TrainCarKind.WAGON, value=11),
        TrainCar(kind=TrainCarKind.WAGON, value=12),
        TrainCar(kind=TrainCarKind.WAGON, value=13),
        TrainCar(kind=TrainCarKind.WAGON, value=14),
    ]
    bandits = [
        Bandit("p0", "P0", Position(car_index=3, level=Level.INSIDE, lane=0), Direction.TOWARD_LOCOMOTIVE),
        Bandit("p1", "P1", Position(car_index=4, level=Level.ROOF, lane=0), Direction.TOWARD_TAIL),
        Bandit("p2", "P2", Position(car_index=5, level=Level.INSIDE, lane=0), Direction.TOWARD_TAIL),
    ]
    return GameState(train=train, bandits=bandits, phase=Phase.ROBBERY, round_number=1, first_player_id="p0")


def test_end_round_detaches_and_awards() -> None:
    state = _controlled_state()
    events = end_round(state)
    # хвостовой вагон (car 5) отцеплен
    assert len(state.train) == 5
    assert state.last_wagon_index == 4
    # p2 был в car 5 -> выбыл; ближайший к нему — p1 (car 4, крыша) -> $14
    assert state.bandit_by_id("p2").eliminated is True
    assert state.bandit_by_id("p1").money == 14
    assert state.bandit_by_id("p0").money == 0
    # новый раунд
    assert state.round_number == 2
    assert state.phase is Phase.PLANNING
    assert state.first_player_id == "p1"
    types = {e.type for e in events}
    assert {"wagon_detached", "money_awarded", "eliminated", "round_started"} <= types


def test_end_round_roof_priority() -> None:
    state = _controlled_state()
    state.bandit_by_id("p0").position = Position(car_index=4, level=Level.INSIDE, lane=0)
    state.bandit_by_id("p1").position = Position(car_index=4, level=Level.ROOF, lane=0)
    state.bandit_by_id("p2").position = Position(car_index=2, level=Level.INSIDE, lane=0)
    end_round(state)
    assert state.bandit_by_id("p1").money == 14  # крыша приоритетна
    assert state.bandit_by_id("p0").money == 0


def test_end_round_closest_when_nearest_empty() -> None:
    state = _controlled_state()
    state.bandit_by_id("p0").position = Position(car_index=3, level=Level.INSIDE, lane=0)
    state.bandit_by_id("p1").position = Position(car_index=5, level=Level.INSIDE, lane=0)  # в отцепленном
    state.bandit_by_id("p2").position = Position(car_index=2, level=Level.INSIDE, lane=0)
    end_round(state)
    # p1 выбывает; ближайший к отцепленному (car 5) — p0 (car 3), т.к. car 4 пуст
    assert state.bandit_by_id("p1").eliminated is True
    assert state.bandit_by_id("p0").money == 14
    assert state.bandit_by_id("p2").money == 0

def test_end_round_finishes_richest_when_no_wagons() -> None:
    state = _controlled_state()
    state.train = state.train[:3]  # [Делориан, локомотив, w1($11)]
    state.bandit_by_id("p0").position = Position(car_index=1, level=Level.INSIDE, lane=0)
    state.bandit_by_id("p1").position = Position(car_index=1, level=Level.ROOF, lane=0)
    state.bandit_by_id("p0").money = 3
    state.bandit_by_id("p1").money = 7
    state.bandit_by_id("p2").eliminated = True
    events = end_round(state)
    # два активных на локомотиве, вагонов не осталось -> богатейший p1
    assert state.phase is Phase.FINISHED
    assert state.winner_id == "p1"
    assert "game_finished" in [e.type for e in events]

def test_end_round_prone_still_closest() -> None:
    state = _controlled_state()
    state.bandit_by_id("p1").posture = Posture.PRONE  # лежит, но ближе всех к car 5
    end_round(state)
    assert state.bandit_by_id("p1").money == 14
