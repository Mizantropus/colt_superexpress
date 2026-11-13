"""Тесты состояния игры."""

from app.game.models import (
    Bandit,
    Direction,
    Level,
    Position,
    TrainCar,
    TrainCarKind,
)
from app.game.state import GameState, Phase


def _bandit(pid: str) -> Bandit:
    return Bandit(
        player_id=pid,
        name=pid,
        position=Position(car_index=3, level=Level.INSIDE, lane=0),
        direction=Direction.TOWARD_LOCOMOTIVE,
    )


def _train(wagon_count: int = 3) -> list[TrainCar]:
    cars = [TrainCar(kind=TrainCarKind.DELOREAN), TrainCar(kind=TrainCarKind.LOCOMOTIVE)]
    cars += [TrainCar(kind=TrainCarKind.WAGON, value=11 + i) for i in range(wagon_count)]
    return cars


def test_state_defaults() -> None:
    state = GameState()
    assert state.phase is Phase.PLANNING
    assert state.round_number == 1
    assert state.train == []
    assert state.bandits == []
    assert not state.is_finished


def test_train_helpers() -> None:
    state = GameState(train=_train(3))
    assert state.wagon_count == 3
    assert state.last_wagon_index == 4  # 0 Делориан, 1 локомотив, 2..4 вагоны
    assert state.wagon_indices == [2, 3, 4]


def test_turn_order_rotation() -> None:
    bandits = [_bandit("a"), _bandit("b"), _bandit("c")]
    state = GameState(train=_train(3), bandits=bandits, first_player_id="b")
    order = [b.player_id for b in state.turn_order()]
    assert order == ["b", "c", "a"]


def test_active_bandits_filters_eliminated() -> None:
    bandits = [_bandit("a"), _bandit("b"), _bandit("c")]
    bandits[1].eliminated = True
    state = GameState(train=_train(3), bandits=bandits, first_player_id="a")
    assert [b.player_id for b in state.active_bandits()] == ["a", "c"]
    assert [b.player_id for b in state.turn_order()] == ["a", "c"]


def test_next_player_id() -> None:
    bandits = [_bandit("a"), _bandit("b"), _bandit("c")]
    state = GameState(train=_train(3), bandits=bandits, first_player_id="a")
    assert state.next_player_id("a") == "b"
    assert state.next_player_id("c") == "a"
    assert state.next_player_id(None) == "a"


def test_bandit_lookup() -> None:
    bandits = [_bandit("a"), _bandit("b")]
    state = GameState(train=_train(2), bandits=bandits, current_player_id="b")
    assert state.bandit_by_id("a") is bandits[0]
    assert state.current_bandit is bandits[1]
    assert state.bandit_by_id("zzz") is None


def test_record_event() -> None:
    state = GameState(train=_train(2), bandits=[_bandit("a")])
    state.record_event("shoot", target="b")
    assert len(state.history) == 1
    assert state.history[0].type == "shoot"
    assert state.history[0].round_number == 1