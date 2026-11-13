import sys, time, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.planning import submit_plan, start_robbery
from app.game.engine import resolve_round
from app.game.models import Action
from app.game.state import Phase

ALL = list(Action)

def run_game(n, rng, max_rounds=80):
    players = [(f"p{i}", f"P{i}") for i in range(n)]
    state = setup_game(players, rng=rng)
    rounds = 0
    while state.phase is not Phase.FINISHED and rounds < max_rounds:
        for pid in [b.player_id for b in state.bandits if not b.eliminated]:
            acts = list(ALL)
            rng.shuffle(acts)
            submit_plan(state, pid, acts[:3])
        start_robbery(state)
        t0 = time.time()
        events = resolve_round(state)
        dt = time.time() - t0
        if dt > 3.0:
            print(f"SLOW: n={n} round={rounds} dt={dt:.2f}s events={len(events)}")
        rounds += 1
    return rounds, state

rng = random.Random(123)
crashes = 0
for i in range(500):
    n = rng.randint(3, 7)
    rrng = random.Random(i * 999 + n)
    try:
        run_game(n, rrng)
    except Exception as e:
        crashes += 1
        print(f"CRASH game {i} n={n}: {e!r}")
print(f"stress: 500 games, crashes={crashes}")