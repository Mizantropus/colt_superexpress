"""Тесты доменной модели."""

from app.game.models import (
    WAGON_VALUES,
    Action,
    assign_lane,
    Bandit,
    Direction,
    Level,
    Posture,
    Position,
    TrainCar,
    TrainCarKind,
)


def test_wagon_values() -> None:
    assert WAGON_VALUES == (11, 12, 13, 14, 15, 16, 17, 18)
    assert len(WAGON_VALUES) == 8


def test_action_count() -> None:
    assert len(list(Action)) == 6


def test_direction_opposite() -> None:
    assert Direction.TOWARD_LOCOMOTIVE.opposite() is Direction.TOWARD_TAIL
    assert Direction.TOWARD_TAIL.opposite() is Direction.TOWARD_LOCOMOTIVE



def test_bandit_defaults() -> None:
    bandit = Bandit(
        player_id="p1",
        name="Бандит",
        position=Position(car_index=3, level=Level.INSIDE, lane=0),
        direction=Direction.TOWARD_LOCOMOTIVE,
    )
    assert bandit.posture is Posture.STANDING
    assert not bandit.is_prone


def test_train_car() -> None:
    wagon = TrainCar(kind=TrainCarKind.WAGON, value=15)
    locomotive = TrainCar(kind=TrainCarKind.LOCOMOTIVE)
    assert wagon.value == 15
    assert locomotive.value is None

def test_assign_lane_from_tail_shifts() -> None:
    a = Bandit("a", "A", Position(car_index=3, level=Level.INSIDE, lane=0), Direction.TOWARD_LOCOMOTIVE)
    b = Bandit("b", "B", Position(car_index=3, level=Level.INSIDE, lane=1), Direction.TOWARD_TAIL)
    lane = assign_lane([a, b], from_tail=True)
    assert lane == 0
    assert a.position.lane == 1
    assert b.position.lane == 2


def test_assign_lane_from_head_appends() -> None:
    a = Bandit("a", "A", Position(car_index=3, level=Level.INSIDE, lane=0), Direction.TOWARD_LOCOMOTIVE)
    lane = assign_lane([a], from_tail=False)
    assert lane == 1
    assert a.position.lane == 0
