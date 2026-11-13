import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

import random
from app.game.setup import setup_game
from app.game.planning import submit_plan, start_robbery
from app.game.engine import resolve_round
from app.game.models import Action
from app.game.state import Phase

ALL_ACTIONS = list(Action)

def run_game(n, rng, max_rounds=60):
    players = [(f"p{i}", f"P{i}") for i in range(n)]
    state = setup_game(players, rng=rng)
    rounds = 0
    while state.phase is not Phase.FINISHED and rounds < max_rounds:
        for pid in [b.player_id for b in state.bandits if not b.eliminated]:
            acts = list(ALL_ACTIONS)
            rng.shuffle(acts)
            submit_plan(state, pid, acts[:3])
        start_robbery(state)
        resolve_round(state)
        rounds += 1
    return rounds, state

rng = random.Random(12345)
rounds, state = run_game(3, rng)
print("smoke 3p:", rounds, "rounds, phase", state.phase.value, "winner", state.winner_id)

crashes = 0
draws = 0
for i in range(30):
    n = rng.randint(3, 7)
    rrng = random.Random(i * 1000 + n)
    try:
        rounds, st = run_game(n, rrng)
        if st.phase is Phase.FINISHED and st.winner_id is None:
            draws += 1
    except Exception as e:
        crashes += 1
        print("CRASH game", i, "n=", n, repr(e))
print("stress: 30 games, crashes=", crashes, "draws=", draws)