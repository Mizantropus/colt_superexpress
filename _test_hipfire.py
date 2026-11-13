import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.planning import submit_plan, start_robbery
from app.game.engine import resolve_round
from app.game.models import Action, Direction, Level, Posture, Position

state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])

a = state.bandit_by_id("A")
a.posture = Posture.STANDING
a.position = Position(car_index=3, level=Level.INSIDE, lane=0)
a.direction = Direction.TOWARD_LOCOMOTIVE

b = state.bandit_by_id("B")
b.posture = Posture.STANDING
b.position = Position(car_index=2, level=Level.INSIDE, lane=0)
b.direction = Direction.TOWARD_TAIL

submit_plan(state, "A", [Action.HIP_FIRE, Action.MOVE, Action.SHOOT])
submit_plan(state, "B", [Action.MOVE, Action.SHOOT, Action.TURN_AROUND])
submit_plan(state, "C", [Action.MOVE, Action.SHOOT, Action.TURN_AROUND])

start_robbery(state)
events = resolve_round(state)

print("=== A (standing hip fire) events ===")
for e in events:
    if e.data.get("player_id") == "A":
        print(" ", e.type, e.data)

print("=== B knocked? ===")
for e in events:
    if e.data.get("player_id") == "B" and e.type in ("knocked", "knocked_off_train"):
        print(" ", e.type, e.data)
print("done")