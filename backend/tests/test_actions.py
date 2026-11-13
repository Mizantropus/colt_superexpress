"""Тесты действия «Переместиться»."""

import random

import pytest

from app.game.actions import apply_change_level, apply_hip_fire, apply_horse, apply_move, apply_shoot, apply_turn_around
from app.game.models import Direction, Level, LOCOMOTIVE_INDEX, Position, Posture
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


def test_move_toward_locomotive() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=4, direction=Direction.TOWARD_LOCOMOTIVE)
    events = apply_move(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.car_index == 3
    assert b.position.lane == 0
    assert b.position.level is Level.INSIDE
    assert events[0].type == "moved"


def test_move_toward_tail() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=2, direction=Direction.TOWARD_TAIL)
    apply_move(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.car_index == 3
    assert b.position.lane == 1


def test_move_preserves_level() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, level=Level.ROOF, direction=Direction.TOWARD_TAIL)
    apply_move(state, "p0")
    assert state.bandit_by_id("p0").position.level is Level.ROOF


def test_move_into_delorean() -> None:
    state = _state(3)
    # локомотив (car_index 1), смотрит на голову
    _bandit_at(state, "p0", car_index=1, direction=Direction.TOWARD_LOCOMOTIVE)
    events = apply_move(state, "p0")
    assert events[0].type == "delorean_entered"
    # телепортирован в хвост: внутрь последнего вагона, лицом к локомотиву
    b = state.bandit_by_id("p0")
    assert b.position.car_index == state.last_wagon_index
    assert b.position.level is Level.INSIDE
    assert b.direction is Direction.TOWARD_LOCOMOTIVE


def test_move_off_train() -> None:
    state = _state(3)
    last = state.last_wagon_index
    _bandit_at(state, "p0", car_index=last, direction=Direction.TOWARD_TAIL)
    events = apply_move(state, "p0")
    assert events[0].type == "moved_off_train"
    assert state.bandit_by_id("p0").off_train is True


def test_move_invalid_eliminated() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_TAIL)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_move(state, "p0")

def test_change_level_inside_to_roof() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, level=Level.INSIDE, lane=1)
    events = apply_change_level(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.level is Level.ROOF
    assert b.position.car_index == 3
    assert b.position.lane == 0
    assert events[0].type == "changed_level"


def test_change_level_roof_to_inside() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, level=Level.ROOF)
    apply_change_level(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.level is Level.INSIDE
    assert b.position.lane == 0


def test_change_level_eliminated_raises() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_change_level(state, "p0")

def test_turn_around() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_LOCOMOTIVE)
    events = apply_turn_around(state, "p0")
    assert state.bandit_by_id("p0").direction is Direction.TOWARD_TAIL
    assert events[0].type == "turned_around"


def test_turn_around_back() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_TAIL)
    apply_turn_around(state, "p0")
    assert state.bandit_by_id("p0").direction is Direction.TOWARD_LOCOMOTIVE


def test_turn_around_eliminated_raises() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_turn_around(state, "p0")

def test_shoot_hits_nearest_toward_head() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=5, direction=Direction.TOWARD_LOCOMOTIVE)
    _bandit_at(state, "p1", car_index=3)
    _bandit_at(state, "p2", car_index=1)
    events = apply_shoot(state, "p0")
    b1 = state.bandit_by_id("p1")
    assert b1.position.car_index == 2
    assert b1.posture is Posture.PRONE
    assert b1.position.lane == 0
    assert state.bandit_by_id("p2").posture is Posture.STANDING
    assert [e.type for e in events] == ["shoot", "knocked"]


def test_shoot_toward_tail() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=2, direction=Direction.TOWARD_TAIL)
    _bandit_at(state, "p1", car_index=4)
    _bandit_at(state, "p2", car_index=1)
    apply_shoot(state, "p0")
    b1 = state.bandit_by_id("p1")
    assert b1.position.car_index == 5
    assert b1.posture is Posture.PRONE
    assert b1.position.lane == 0


def test_shoot_miss() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_LOCOMOTIVE)
    _bandit_at(state, "p1", car_index=4)
    _bandit_at(state, "p2", car_index=5)
    events = apply_shoot(state, "p0")
    assert len(events) == 1
    assert events[0].type == "shoot"
    assert events[0].data["target_id"] is None


def test_shoot_ignores_other_level() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, level=Level.ROOF, direction=Direction.TOWARD_TAIL)
    _bandit_at(state, "p1", car_index=4, level=Level.INSIDE)
    events = apply_shoot(state, "p0")
    assert events[0].data["target_id"] is None


def test_shoot_knocks_off_train() -> None:
    state = _state(3)
    last = state.last_wagon_index
    _bandit_at(state, "p0", car_index=last - 1, direction=Direction.TOWARD_TAIL)
    _bandit_at(state, "p1", car_index=last)
    _bandit_at(state, "p2", car_index=2)
    events = apply_shoot(state, "p0")
    assert state.bandit_by_id("p1").off_train is True
    assert [e.type for e in events] == ["shoot", "knocked_off_train"]


def test_shoot_knocks_into_delorean() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=2, direction=Direction.TOWARD_LOCOMOTIVE)
    _bandit_at(state, "p1", car_index=1)
    _bandit_at(state, "p2", car_index=3)
    events = apply_shoot(state, "p0")
    assert [e.type for e in events] == ["shoot", "delorean_entered"]
    assert state.bandit_by_id("p1").position.car_index == state.last_wagon_index


def test_shoot_hits_front_edge_in_same_car() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, lane=0, direction=Direction.TOWARD_LOCOMOTIVE)
    _bandit_at(state, "p1", car_index=3, lane=1)
    _bandit_at(state, "p2", car_index=2)
    events = apply_shoot(state, "p0")
    assert events[0].data["target_id"] == "p1"
    assert state.bandit_by_id("p1").position.car_index == 2


def test_shoot_eliminated_raises() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_TAIL)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_shoot(state, "p0")

def test_horse_teleports_to_locomotive() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=4, level=Level.INSIDE, direction=Direction.TOWARD_TAIL)
    events = apply_horse(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.position.car_index == LOCOMOTIVE_INDEX
    assert b.position.level is Level.ROOF
    assert b.direction is Direction.TOWARD_LOCOMOTIVE
    assert b.posture is Posture.STANDING
    assert events[0].type == "horse"


def test_horse_saves_off_train() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=4)
    state.bandit_by_id("p0").off_train = True
    apply_horse(state, "p0")
    b = state.bandit_by_id("p0")
    assert b.off_train is False
    assert b.position.car_index == LOCOMOTIVE_INDEX
    assert b.position.level is Level.ROOF


def test_horse_eliminated_raises() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=4)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_horse(state, "p0")

def test_hip_fire_prone_stands_and_shoots() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_TAIL)
    state.bandit_by_id("p0").posture = Posture.PRONE
    _bandit_at(state, "p1", car_index=4)
    _bandit_at(state, "p2", car_index=1)
    events = apply_hip_fire(state, "p0")
    p0 = state.bandit_by_id("p0")
    p1 = state.bandit_by_id("p1")
    assert p0.posture is Posture.STANDING
    assert p1.posture is Posture.PRONE
    assert p1.position.car_index == 5
    assert events[0].type == "stood_up"
    assert "shoot" in [e.type for e in events]


def test_hip_fire_standing_lies_down() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3, direction=Direction.TOWARD_TAIL)
    _bandit_at(state, "p1", car_index=4)
    _bandit_at(state, "p2", car_index=1)
    events = apply_hip_fire(state, "p0")
    assert state.bandit_by_id("p0").posture is Posture.PRONE
    assert state.bandit_by_id("p1").position.car_index == 4
    assert state.bandit_by_id("p1").posture is Posture.STANDING
    assert events[0].type == "lay_down"
    assert "shoot" not in [e.type for e in events]


def test_hip_fire_eliminated_raises() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=3)
    state.bandit_by_id("p0").eliminated = True
    with pytest.raises(ValueError):
        apply_hip_fire(state, "p0")

def test_shoot_skips_prone() -> None:
    state = _state(3)
    _bandit_at(state, "p0", car_index=5, direction=Direction.TOWARD_LOCOMOTIVE)
    _bandit_at(state, "p1", car_index=3)
    state.bandit_by_id("p1").posture = Posture.PRONE
    _bandit_at(state, "p2", car_index=2)
    events = apply_shoot(state, "p0")
    # пуля пролетает над лежачим p1 и попадает в стоящего p2
    assert events[0].data["target_id"] == "p2"
    assert state.bandit_by_id("p1").posture is Posture.PRONE
    assert state.bandit_by_id("p2").posture is Posture.PRONE
    assert state.bandit_by_id("p2").position.car_index == 1
