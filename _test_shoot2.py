import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.actions import apply_move, apply_shoot
from app.game.models import Direction, Level, Position

state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])

a = state.bandit_by_id("A")
b = state.bandit_by_id("B")

# Оба в первом вагоне (index 2), внутри, смотрят вперёд.
a.position = Position(car_index=2, level=Level.INSIDE, lane=0)
a.direction = Direction.TOWARD_LOCOMOTIVE
b.position = Position(car_index=2, level=Level.INSIDE, lane=1)
b.direction = Direction.TOWARD_LOCOMOTIVE

# Перемещаемся вперёд в локомотив (A первым, B вторым).
apply_move(state, "A")
apply_move(state, "B")
print("После перемещений: A", a.position, "| B", b.position)

# Кто ближе к хвосту (lane 0) — тот стреляет вперёд.
shooter_id = "A" if a.position.lane == 0 else "B"
print("Стреляет:", shooter_id)

events = apply_shoot(state, shooter_id)
print("events:", [e.type for e in events])
for e in events:
    print("  ", e.type, e.data)