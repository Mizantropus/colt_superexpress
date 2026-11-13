"""Оркестрация онлайн-партии (планирование + ограбление)."""

from __future__ import annotations

import asyncio
import random
import time

from app.game.bots import choose_plan
from app.game.engine import resolve_round
from app.game.planning import all_plans_submitted, start_planning, start_robbery, submit_plan
from app.game.round_end import begin_next_round
from app.game.setup import setup_game
from app.game.state import GameEvent, GameState, Phase
from app.ws.rooms import Room, RoomStatus

PLANNING_TIMEOUT_SECONDS = 60.0


def start_game(room: Room, rng: random.Random | None = None) -> GameState:
    """Создаёт партию для комнаты и начинает первый раунд (планирование)."""
    players = [(p.id, p.name) for p in room.ordered_players()]
    state = setup_game(players, rng=rng)
    room.game_state = state
    room.status = RoomStatus.PLAYING
    start_planning(state)
    return state


def begin_round(room: Room, rng: random.Random | None = None) -> list[str]:
    """Начинает фазу планирования нового раунда и автоподаёт планы ботов."""
    state = room.game_state
    if state is None:
        return []
    start_planning(state)
    return auto_submit_bots(room, rng)


def auto_submit_bots(room: Room, rng: random.Random | None = None) -> list[str]:
    """Подаёт планы за ботов. Возвращает id ботов."""
    state = room.game_state
    if state is None:
        return []
    rng = rng or random.Random()
    submitted: list[str] = []
    for player in room.ordered_players():
        if not player.is_bot or player.id in state.plans:
            continue
        bandit = state.bandit_by_id(player.id)
        if bandit is None or bandit.eliminated:
            continue
        submit_plan(state, player.id, choose_plan(state, player.id, rng))
        submitted.append(player.id)
    return submitted


def fill_missing_plans(room: Room, rng: random.Random | None = None) -> list[str]:
    """Заполняет планы случайными для не подавших игроков (по таймеру)."""
    state = room.game_state
    if state is None:
        return []
    rng = rng or random.Random()
    filled: list[str] = []
    for bandit in state.active_bandits():
        if bandit.player_id not in state.plans:
            submit_plan(state, bandit.player_id, choose_plan(state, bandit.player_id, rng))
            filled.append(bandit.player_id)
    return filled


def planning_done(room: Room) -> bool:
    state = room.game_state
    return state is not None and all_plans_submitted(state)


def start_robbery_phase(room: Room) -> bool:
    """Переходит к фазе ограбления (если все планы поданы)."""
    state = room.game_state
    if state is None or not all_plans_submitted(state):
        return False
    start_robbery(state)
    return True


async def wait_for_planning(room: Room, timeout_seconds: float, rng: random.Random | None = None) -> bool:
    """Ждёт, пока все подадут планы, или таймаут (заполняет случайными).

    Возвращает True, если сработал таймаут.
    """
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if planning_done(room):
            return False
        await asyncio.sleep(0.05)
    if not planning_done(room):
        fill_missing_plans(room, rng)
    return True


def run_robbery(room: Room) -> list[GameEvent]:
    """Разрешает фазу ограбления (синхронно) и возвращает события."""
    state = room.game_state
    if state is None or not all_plans_submitted(state):
        return []
    start_robbery(state)
    return [state.record_event("robbery_started")] + resolve_round(state)


async def wait_for_round_confirm(room: Room) -> None:
    """Ждёт, пока все подключённые игроки-люди закроют окошко результата раунда."""
    expected = {p.id for p in room.players.values() if not p.is_bot and p.connected}
    while True:
        if expected.issubset(room.round_confirmations):
            return
        await asyncio.sleep(0.05)


async def run_game(
    room: Room,
    on_event,
    planning_timeout: float = PLANNING_TIMEOUT_SECONDS,
    step_delay: float = 0.0,
    rng: random.Random | None = None,
    state_store=None,
) -> None:
    """Полный онлайн-цикл партии (предполагает, что start_game уже вызван).

    on_event — async-колбэк (событие -> ...), вызывается строго по порядку.
    step_delay — пауза между событиями (таймер на ход, для анимаций).
    """
    while room.status is RoomStatus.PLAYING and room.game_state is not None:
        auto_submit_bots(room, rng)
        timed_out = await wait_for_planning(room, planning_timeout, rng)
        if timed_out:
            await on_event(room.game_state.record_event("planning_timed_out"))

        events = run_robbery(room)
        for event in events:
            await on_event(event)
            if step_delay:
                await asyncio.sleep(step_delay)

        if state_store is not None and room.game_state is not None:
            await state_store.save(room.code, room.game_state)

        if room.game_state.phase is Phase.FINISHED:
            room.status = RoomStatus.FINISHED
            break

        # Ждём, пока все игроки закроют окошко результата раунда,
        # и только потом начинаем следующий раунд (таймер стартует с этого момента).
        room.round_confirmations.clear()
        await wait_for_round_confirm(room)
        room.round_confirmations.clear()

        event = begin_next_round(room.game_state)
        deadline = time.time() + planning_timeout + step_delay
        event.data["planning_deadline"] = deadline
        room.planning_deadline = deadline
        await on_event(event)
