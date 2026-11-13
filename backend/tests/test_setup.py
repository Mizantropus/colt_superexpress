"""Тесты инициализации партии."""

import random

import pytest

from app.game.models import Direction, Level, TrainCarKind
from app.game.setup import build_train, setup_game


def test_build_train_structure() -> None:
    train = build_train(4)
    assert len(train) == 2 + 5  # Делориан + локомотив + 5 вагонов
    assert train[0].kind is TrainCarKind.DELOREAN
    assert train[1].kind is TrainCarKind.LOCOMOTIVE
    assert all(car.kind is TrainCarKind.WAGON for car in train[2:])
    values = [car.value for car in train[2:]]
    assert len(values) == 5
    assert len(set(values)) == 5
    assert set(values) <= set(range(11, 19))


def test_build_train_all_values_for_7_players() -> None:
    train = build_train(7)
    values = sorted(car.value for car in train[2:])
    assert values == [11, 12, 13, 14, 15, 16, 17, 18]


def test_build_train_invalid_players() -> None:
    for n in (0, 1, 2, 8, 9):
        with pytest.raises(ValueError):
            build_train(n)


def test_setup_placement() -> None:
    players = [("a", "Аня"), ("b", "Боря"), ("c", "Витя"), ("d", "Гоша")]
    state = setup_game(players, first_player_id="b", rng=random.Random(0))
    assert state.first_player_id == "b"
    assert len(state.bandits) == 4
    by_id = {b.player_id: b for b in state.bandits}
    # порядок хода b,c,d,a -> вагоны 4,3,2,1 (car_index 5,4,3,2)
    assert by_id["b"].position.car_index == 5
    assert by_id["c"].position.car_index == 4
    assert by_id["d"].position.car_index == 3
    assert by_id["a"].position.car_index == 2
    assert all(b.position.level is Level.INSIDE for b in state.bandits)


def test_setup_directions_even() -> None:
    players = [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")]
    state = setup_game(players, first_player_id="a", rng=random.Random(0))
    by_id = {b.player_id: b for b in state.bandits}
    # порядок хода a,b,c,d; ближние к локомотиву (d,c) на хвост, остальные (b,a) на локомотив
    assert by_id["a"].direction is Direction.TOWARD_LOCOMOTIVE
    assert by_id["b"].direction is Direction.TOWARD_LOCOMOTIVE
    assert by_id["c"].direction is Direction.TOWARD_TAIL
    assert by_id["d"].direction is Direction.TOWARD_TAIL


def test_setup_directions_odd() -> None:
    players = [("a", "A"), ("b", "B"), ("c", "C")]
    state = setup_game(players, first_player_id="a", rng=random.Random(0))
    by_id = {b.player_id: b for b in state.bandits}
    # ближний к локомотиву (c) на хвост; центральный (b) и ближний к хвосту (a) на локомотив
    assert by_id["a"].direction is Direction.TOWARD_LOCOMOTIVE
    assert by_id["b"].direction is Direction.TOWARD_LOCOMOTIVE
    assert by_id["c"].direction is Direction.TOWARD_TAIL


def test_setup_turn_order_consistency() -> None:
    players = [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")]
    state = setup_game(players, first_player_id="c", rng=random.Random(0))
    assert [b.player_id for b in state.turn_order()] == ["c", "d", "a", "b"]


def test_setup_random_first_player() -> None:
    players = [("a", "A"), ("b", "B"), ("c", "C")]
    state = setup_game(players, rng=random.Random(42))
    assert state.first_player_id in {"a", "b", "c"}