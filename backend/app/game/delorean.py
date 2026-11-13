"""Механика «Делориана» (Машины времени)."""

from __future__ import annotations

from app.game.elimination import eliminate_bandit
from app.game.models import Direction, Level, Position, Posture, assign_lane
from app.game.state import GameEvent, GameState


def apply_delorean_entry(state: GameState, player_id: str, cause: str = "move") -> list[GameEvent]:
    """Обрабатывает вход бандита в Делориан.

    Первый вход за раунд: телепорт в хвост поезда (внутрь последнего вагона,
    лицом к локомотиву) и перемотка сыгранных карт (played_count сбрасывается,
    бандит повторит свои действия). Повторный вход — временной парадокс,
    бандит выбывает.
    """
    bandit = state.bandit_by_id(player_id)
    if bandit is None or bandit.eliminated:
        raise ValueError("Бандит не может войти в Делориан")

    # Временной парадокс: повторный вход за один раунд.
    if player_id in state.delorean_entered:
        events = eliminate_bandit(state, player_id)
        events.append(state.record_event("time_paradox", player_id=player_id))
        return events

    # Первый вход за раунд.
    state.delorean_entered.add(player_id)

    # Телепорт в хвост: внутрь последнего вагона, лицом к локомотиву (lane=0).
    lane, shifted = assign_lane(state.bandits_in_cell(state.last_wagon_index, Level.INSIDE), from_tail=True)
    bandit.position = Position(
        car_index=state.last_wagon_index,
        level=Level.INSIDE,
        lane=lane,
    )
    bandit.direction = Direction.TOWARD_LOCOMOTIVE
    bandit.posture = Posture.STANDING
    bandit.off_train = False

    # Перемотка: сыгранные в этом раунде карты возвращаются в стопку.
    state.played_counts[player_id] = 0

    return [state.record_event(
        "delorean_entered",
        player_id=player_id,
        car_index=state.last_wagon_index,
        level=Level.INSIDE.value,
        lane=lane,
        direction=Direction.TOWARD_LOCOMOTIVE.value,
        shifted=shifted,
        cause=cause,
    )]