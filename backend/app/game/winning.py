"""Условия победы."""

from __future__ import annotations

from app.game.models import Level
from app.game.state import GameState


def check_winner(state: GameState) -> tuple[bool, str | None]:
    """Проверяет завершение партии.

    Возвращает (игра_завершена, победитель):
    - один активный бандит остался — он победитель;
    - все выбыли — ничья (победитель None);
    - отцеплен последний вагон (нет вагонов) — побеждает богатейший;
      при равенстве сумм — крыша локомотива, затем ближе к хвосту;
    - иначе игра продолжается.
    """
    active = state.active_bandits()

    if len(active) == 1:
        return True, active[0].player_id

    if len(active) == 0:
        return True, None

    if state.wagon_count == 0:
        order_by_id = {b.player_id: i for i, b in enumerate(state.bandits)}
        winner = max(
            active,
            key=lambda b: (
                b.money,
                1 if b.position.level is Level.ROOF else 0,   # крыша приоритетна
                b.position.car_index,                         # ближе к хвосту
                -b.position.lane,                            # меньше lane — ближе к хвосту
                -order_by_id[b.player_id],                    # детерминированный fallback
            ),
        )
        return True, winner.player_id

    return False, None