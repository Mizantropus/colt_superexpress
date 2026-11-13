"""Тесты оркестрации партии (планирование)."""

import asyncio
import random

from app.game.models import Action
from app.game.planning import submit_plan
from app.game.state import Phase
from app.ws.rooms import Player, RoomRegistry
from app.ws.session import (
    auto_submit_bots,
    fill_missing_plans,
    planning_done,
    start_game,
    start_robbery_phase,
    wait_for_planning,
)


def _room():
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    room.add_bot(bot_id="bot_1")
    room.add_player(Player(id="a", name="Аня"))
    room.add_player(Player(id="b", name="Боря"))
    return room


def test_start_game_creates_state() -> None:
    room = _room()
    state = start_game(room, rng=random.Random(0))
    assert room.game_state is state
    assert room.status.value == "playing"
    assert state.phase is Phase.PLANNING
    assert len(state.bandits) == 4  # хост + бот + 2 человека


def test_auto_submit_bots() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))
    submitted = auto_submit_bots(room)
    assert submitted == ["bot_1"]
    assert "bot_1" in room.game_state.plans


def test_planning_done_and_robbery() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))
    auto_submit_bots(room)
    assert not planning_done(room)
    for pid in ("h", "a", "b"):
        submit_plan(room.game_state, pid, [Action.MOVE, Action.SHOOT, Action.HORSE])
    assert planning_done(room)
    assert start_robbery_phase(room) is True
    assert room.game_state.phase is Phase.ROBBERY


def test_fill_missing_plans() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))
    filled = fill_missing_plans(room, rng=random.Random(1))
    assert len(filled) == 4
    assert planning_done(room)


def test_wait_for_planning_timeout() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))

    async def scenario():
        return await wait_for_planning(room, 0.1, rng=random.Random(1))

    assert asyncio.run(scenario()) is True
    assert planning_done(room)


def test_wait_for_planning_all_submitted() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))

    async def scenario():
        async def submit_all():
            await asyncio.sleep(0.02)
            for pid in ("h", "a", "b", "bot_1"):
                submit_plan(room.game_state, pid, [Action.MOVE, Action.SHOOT, Action.HORSE])

        task = asyncio.create_task(submit_all())
        result = await wait_for_planning(room, 1.0)
        await task
        return result

    assert asyncio.run(scenario()) is False