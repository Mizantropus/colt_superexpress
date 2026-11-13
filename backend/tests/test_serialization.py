"""Тесты сериализации GameState."""

import json
import random

from app.game.models import Action
from app.game.planning import submit_plan
from app.game.serialization import state_from_dict, state_to_dict
from app.game.setup import setup_game


def _state():
    players = [("p0", "P0"), ("p1", "P1"), ("p2", "P2")]
    state = setup_game(players, first_player_id="p0", rng=random.Random(0))
    submit_plan(state, "p0", [Action.MOVE, Action.SHOOT, Action.HORSE])
    state.bandits[0].money = 15
    state.bandits[1].eliminated = True
    state.delorean_entered.add("p2")
    state.record_event("test_event", foo="bar")
    return state


def test_roundtrip() -> None:
    state = _state()
    restored = state_from_dict(state_to_dict(state))

    assert restored.phase is state.phase
    assert restored.round_number == state.round_number
    assert restored.first_player_id == state.first_player_id
    assert [c.kind for c in restored.train] == [c.kind for c in state.train]
    assert [c.value for c in restored.train] == [c.value for c in state.train]
    assert len(restored.bandits) == len(state.bandits)
    for rb, b in zip(restored.bandits, state.bandits):
        assert rb.player_id == b.player_id
        assert rb.name == b.name
        assert rb.position == b.position
        assert rb.direction is b.direction
        assert rb.posture is b.posture
        assert rb.eliminated == b.eliminated
        assert rb.off_train == b.off_train
        assert rb.money == b.money
    assert restored.plans == state.plans
    assert restored.played_counts == state.played_counts
    assert restored.delorean_entered == state.delorean_entered
    assert [e.type for e in restored.history] == [e.type for e in state.history]


def test_state_to_dict_is_json_serializable() -> None:
    state = _state()
    json.dumps(state_to_dict(state))  # не должно бросать