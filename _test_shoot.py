import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.actions import apply_shoot
from app.game.models import Direction, Level, Position, Posture

state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])

a = state.bandit_by_id("A")
b = state.bandit_by_id("B")

# A — ближе к хвосту (lane 0), B — передний (lane 1). Оба внутри локомотива, смотрят вперёд.
a.position = Position(car_index=1, level=Level.INSIDE, lane=0)
a.direction = Direction.TOWARD_LOCOMOTIVE
b.position = Position(car_index=1, level=Level.INSIDE, lane=1)
b.direction = Direction.TOWARD_LOCOMOTIVE

print("shooter_key =", (a.position.car_index, -a.position.lane))
print("target_key  =", (b.position.car_index, -b.position.lane))

events = apply_shoot(state, "A")
print("events:", [e.type for e in events])
for e in events:
    print("  ", e.type, e.data)
print("B pos:", b.position, "posture:", b.posture)