"""Тесты ограбления онлайн."""

import asyncio
import random

from app.game.models import Action
from app.game.planning import submit_plan
from app.game.state import Phase
from app.ws.rooms import Player, RoomRegistry, RoomStatus
from app.ws.session import auto_submit_bots, run_game, run_robbery, start_game


def _room():
    registry = RoomRegistry()
    room = registry.create(host_id="h", host_name="Хост", max_players=4)
    room.add_bot(bot_id="bot_1")
    room.add_player(Player(id="a", name="Аня"))
    room.add_player(Player(id="b", name="Боря"))
    return room


def test_run_robbery_resolves_round() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))
    auto_submit_bots(room)
    for pid in ("h", "a", "b"):
        submit_plan(room.game_state, pid, [Action.TURN_AROUND, Action.CHANGE_LEVEL, Action.HIP_FIRE])
    events = run_robbery(room)
    assert events
    assert room.game_state.phase in (Phase.PLANNING, Phase.FINISHED)
    assert "wagon_detached" in [e.type for e in events]


def test_run_game_full() -> None:
    room = _room()
    start_game(room, rng=random.Random(0))
    collected = []

    async def on_event(event):
        collected.append(event)

    asyncio.run(run_game(room, on_event, planning_timeout=0.05, rng=random.Random(1)))
    assert room.status is RoomStatus.FINISHED
    assert collected
    assert any(e.type == "game_finished" for e in collected)