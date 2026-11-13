import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.actions import apply_shoot
from app.game.models import Direction, Level, Position

state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])

target = state.bandit_by_id("A")
shooter = state.bandit_by_id("B")

# Цель в локомотиве (car 1), лицом к локомотиву; стрелок в первом вагоне (car 2), стреляет вперёд (со стороны хвоста).
target.position = Position(car_index=1, level=Level.INSIDE, lane=0)
target.direction = Direction.TOWARD_LOCOMOTIVE
shooter.position = Position(car_index=2, level=Level.INSIDE, lane=0)
shooter.direction = Direction.TOWARD_LOCOMOTIVE

events = apply_shoot(state, "B")
for e in events:
    print(e.type, e.data)