"""Сериализация GameState в dict и обратно (для Redis/Postgres)."""

from __future__ import annotations

from app.game.models import (
    Action,
    Bandit,
    Direction,
    Level,
    Position,
    Posture,
    TrainCar,
    TrainCarKind,
)
from app.game.state import GameEvent, GameState, Phase


def state_to_dict(state: GameState) -> dict:
    """Полная сериализация состояния (для серверного хранения)."""
    return {
        "train": [{"kind": c.kind.value, "value": c.value} for c in state.train],
        "bandits": [bandit_to_dict(b) for b in state.bandits],
        "plans": {pid: [a.value for a in actions] for pid, actions in state.plans.items()},
        "played_counts": dict(state.played_counts),
        "delorean_entered": sorted(state.delorean_entered),
        "phase": state.phase.value,
        "round_number": state.round_number,
        "first_player_id": state.first_player_id,
        "current_player_id": state.current_player_id,
        "winner_id": state.winner_id,
        "history": [
            {"type": e.type, "round_number": e.round_number, "data": e.data}
            for e in state.history
        ],
    }


def state_from_dict(data: dict) -> GameState:
    """Восстанавливает GameState из словаря."""
    train = [TrainCar(kind=TrainCarKind(c["kind"]), value=c.get("value")) for c in data["train"]]
    bandits = [bandit_from_dict(b) for b in data["bandits"]]
    plans = {pid: [Action(a) for a in actions] for pid, actions in data.get("plans", {}).items()}
    history = [
        GameEvent(type=e["type"], round_number=e["round_number"], data=e.get("data", {}))
        for e in data.get("history", [])
    ]
    return GameState(
        train=train,
        bandits=bandits,
        plans=plans,
        played_counts=dict(data.get("played_counts", {})),
        delorean_entered=set(data.get("delorean_entered", [])),
        phase=Phase(data["phase"]),
        round_number=data["round_number"],
        first_player_id=data.get("first_player_id"),
        current_player_id=data.get("current_player_id"),
        winner_id=data.get("winner_id"),
        history=history,
    )


def bandit_to_dict(bandit: Bandit) -> dict:
    return {
        "player_id": bandit.player_id,
        "name": bandit.name,
        "car_index": bandit.position.car_index,
        "level": bandit.position.level.value,
        "lane": bandit.position.lane,
        "direction": bandit.direction.value,
        "posture": bandit.posture.value,
        "eliminated": bandit.eliminated,
        "off_train": bandit.off_train,
        "money": bandit.money,
    }


def bandit_from_dict(d: dict) -> Bandit:
    return Bandit(
        player_id=d["player_id"],
        name=d["name"],
        position=Position(
            car_index=d["car_index"],
            level=Level(d["level"]),
            lane=int(d.get("lane", 0)),
        ),
        direction=Direction(d["direction"]),
        posture=Posture(d["posture"]),
        eliminated=d.get("eliminated", False),
        off_train=d.get("off_train", False),
        money=d.get("money", 0),
    )


def public_state(state: GameState) -> dict:
    """Публичное состояние (без планов) для трансляции всем клиентам."""
    data = state_to_dict(state)
    data.pop("plans", None)
    return data
