"""Реализация действий бандитов (по одной функции на действие).

Функции предполагают, что вызываются движком (пункт 20) для стоящего
бандита, находящегося в игре: проверки «лежит навзничь» и «за пределами
поезда» движок выполняет до вызова этих функций.
"""

from __future__ import annotations

from app.game.delorean import apply_delorean_entry
from app.game.models import (
    DELOREAN_INDEX,
    LOCOMOTIVE_INDEX,
    Bandit,
    Direction,
    Level,
    Position,
    Posture,
    assign_lane,
)
from app.game.state import GameEvent, GameState


def apply_move(state: GameState, player_id: str) -> list[GameEvent]:
    """«Переместиться»: на один вагон вперёд по взгляду, на том же уровне.

    Вошедший в вагон становится у края, со стороны которого вошёл.
    """
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated or bandit.off_train:
        raise ValueError("Бандит не может переместиться")

    current = bandit.position.car_index
    direction = bandit.direction
    level = bandit.position.level

    if direction is Direction.TOWARD_LOCOMOTIVE:
        target = current - 1
    else:  # TOWARD_TAIL
        target = current + 1

    # Вошёл в Делориан (телепорт в хвост и перемотка карт).
    if target == DELOREAN_INDEX:
        return apply_delorean_entry(state, player_id, cause="move")

    # Вытолкнут за хвост поезда (выбывание/лошадь — пункты 14, 16).
    if target > state.last_wagon_index:
        bandit.off_train = True
        return [state.record_event("moved_off_train", player_id=player_id)]

    # Обычное перемещение: lane — со стороны входа.
    from_tail = direction is Direction.TOWARD_LOCOMOTIVE
    lane, shifted = assign_lane(state.bandits_in_cell(target, level), from_tail)
    bandit.position = Position(car_index=target, level=level, lane=lane)

    return [state.record_event(
        "moved",
        player_id=player_id,
        from_car=current,
        to_car=target,
        level=level.value,
        lane=lane,
        shifted=shifted,
    )]


def apply_change_level(state: GameState, player_id: str) -> list[GameEvent]:
    """«Сменить уровень»: внутри <-> крыша, вход со стороны хвоста (lane=0)."""
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated or bandit.off_train:
        raise ValueError("Бандит не может сменить уровень")

    pos = bandit.position
    new_level = Level.ROOF if pos.level is Level.INSIDE else Level.INSIDE
    lane, shifted = assign_lane(state.bandits_in_cell(pos.car_index, new_level), from_tail=True)
    bandit.position = Position(car_index=pos.car_index, level=new_level, lane=lane)

    return [state.record_event(
        "changed_level",
        player_id=player_id,
        car_index=pos.car_index,
        level=new_level.value,
        lane=lane,
        shifted=shifted,
    )]


def apply_turn_around(state: GameState, player_id: str) -> list[GameEvent]:
    """«Развернуться»: смена направления взгляда на противоположное."""
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated or bandit.off_train:
        raise ValueError("Бандит не может развернуться")

    bandit.direction = bandit.direction.opposite()

    return [state.record_event(
        "turned_around",
        player_id=player_id,
        direction=bandit.direction.value,
    )]


def apply_shoot(state: GameState, player_id: str, from_hip: bool = False) -> list[GameEvent]:
    """«Выстрел»: пуля летит до первого СТОЯЩЕГО бандита на том же уровне."""
    shooter = state.bandit_by_id(player_id)
    if shooter is None or shooter.eliminated or shooter.off_train:
        raise ValueError("Бандит не может стрелять")

    direction = shooter.direction
    level = shooter.position.level
    target = _find_shoot_target(state, player_id)

    events = [state.record_event(
        "shoot",
        player_id=player_id,
        direction=direction.value,
        target_id=target.player_id if target else None,
        from_hip=from_hip,
    )]

    if target is None:
        return events

    delta = -1 if direction is Direction.TOWARD_LOCOMOTIVE else 1
    new_car = target.position.car_index + delta

    # Отброшен в Делориан (телепорт в хвост и перемотка).
    if new_car == DELOREAN_INDEX:
        events.extend(apply_delorean_entry(state, target.player_id, cause="shoot"))
        return events

    # Отброшен за хвост поезда (выбывание/лошадь — пункты 14, 16).
    if new_car > state.last_wagon_index:
        target.off_train = True
        events.append(state.record_event("knocked_off_train", player_id=target.player_id))
        return events

    # Обычный отброс: на вагон по направлению выстрела + падает навзничь.
    from_tail = direction is Direction.TOWARD_LOCOMOTIVE
    lane, shifted = assign_lane(state.bandits_in_cell(new_car, level), from_tail)
    old_car = target.position.car_index
    target.position = Position(car_index=new_car, level=level, lane=lane)
    target.posture = Posture.PRONE

    events.append(state.record_event(
        "knocked",
        player_id=target.player_id,
        from_car=old_car,
        to_car=new_car,
        level=level.value,
        lane=lane,
        shifted=shifted,
    ))
    return events


def _find_shoot_target(state: GameState, shooter_id: str) -> Bandit | None:
    """Первый СТОЯЩИЙ бандит на уровне стрелка в направлении выстрела (или None).

    Лежачие (prone) пропускаются — пуля летит над ними.
    """
    shooter = state.bandit_by_id(shooter_id)
    if shooter is None:
        return None

    level = shooter.position.level
    direction = shooter.direction
    shooter_key = (shooter.position.car_index, -shooter.position.lane)

    order_by_id = {b.player_id: i for i, b in enumerate(state.bandits)}

    candidates: list[Bandit] = []
    for b in state.active_bandits():
        if b.player_id == shooter_id or b.off_train or b.is_prone:
            continue
        if b.position.level is not level:
            continue
        key = (b.position.car_index, -b.position.lane)
        if direction is Direction.TOWARD_LOCOMOTIVE and key < shooter_key:
            candidates.append(b)
        elif direction is Direction.TOWARD_TAIL and key > shooter_key:
            candidates.append(b)

    if not candidates:
        return None

    candidates.sort(key=lambda b: (b.position.car_index, -b.position.lane, order_by_id[b.player_id]))
    if direction is Direction.TOWARD_LOCOMOTIVE:
        return candidates[-1]   # ближайший к голове
    return candidates[0]        # ближайший к хвосту


def apply_horse(state: GameState, player_id: str) -> list[GameEvent]:
    """«Лошадь»: перенос на крышу локомотива лицом по направлению движения поезда.

    Также спасает бандита, вытолкнутого за пределы поезда (off_train).
    """
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated:
        raise ValueError("Бандит не может сыграть лошадь")

    lane, shifted = assign_lane(state.bandits_in_cell(LOCOMOTIVE_INDEX, Level.ROOF), from_tail=False)
    bandit.position = Position(
        car_index=LOCOMOTIVE_INDEX,
        level=Level.ROOF,
        lane=lane,
    )
    bandit.direction = Direction.TOWARD_LOCOMOTIVE
    bandit.posture = Posture.STANDING
    bandit.off_train = False

    return [state.record_event(
        "horse",
        player_id=player_id,
        car_index=LOCOMOTIVE_INDEX,
        level=Level.ROOF.value,
        lane=lane,
        direction=Direction.TOWARD_LOCOMOTIVE.value,
        shifted=shifted,
    )]


def apply_hip_fire(state: GameState, player_id: str) -> list[GameEvent]:
    """«Выстрел от бедра»: навзничь — встать и выстрелить; иначе — лечь навзничь."""
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated or bandit.off_train:
        raise ValueError("Бандит не может сыграть выстрел от бедра")

    if bandit.is_prone:
        # Встаёт и стреляет в сторону, куда смотрел до падения
        # (направление взгляда при падении не менялось).
        bandit.posture = Posture.STANDING
        events = [state.record_event("stood_up", player_id=player_id)]
        events.extend(apply_shoot(state, player_id, from_hip=True))
        return events

    bandit.posture = Posture.PRONE
    return [state.record_event("lay_down", player_id=player_id)]