"""Боты (ИИ-игроки)."""

from __future__ import annotations

import random

from app.game.models import Action
from app.game.state import GameState


def choose_plan(state: GameState, player_id: str, rng: random.Random | None = None) -> list[Action]:
    """Заглушка-эвристика: случайные 3 разные карты.

    state и player_id пока не используются — полноценный ИИ (оценка позиции,
    угроз, денег) появится в пункте 45.
    """
    rng = rng or random.Random()
    return rng.sample(list(Action), 3)