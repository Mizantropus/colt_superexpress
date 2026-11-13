"""Тесты ботов."""

import random

from app.game.bots import choose_plan
from app.game.models import Action
from app.game.setup import setup_game
from app.ws.rooms import RoomRegistry


def test_choose_plan_returns_three_distinct() -> None:
    players = [("p0", "P0"), ("p1", "P1"), ("p2", "P2")]
    state = setup_game(players, first_player_id="p0", rng=random.Random(0))
    plan = choose_plan(state, "p0", rng=random.Random(1))
    assert len(plan) == 3
    assert len(set(plan)) == 3
    assert all(a in Action for a in plan)


def test_add_bot() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    bot = room.add_bot(name="Бот", bot_id="bot_1")
    assert bot.id == "bot_1"
    assert bot.is_bot is True
    assert "bot_1" in room.players
    assert not room.can_start  # хост + бот = 2


def test_bots_can_make_room_startable() -> None:
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=3)
    room.add_bot(bot_id="bot_1")
    room.add_bot(bot_id="bot_2")
    assert room.can_start  # хост + 2 бота = 3
    assert room.is_full