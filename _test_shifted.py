import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.actions import apply_move
from app.game.models import Direction, Level, Position

state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])

a = state.bandit_by_id("A")
b = state.bandit_by_id("B")

# B в предпоследнем (4), лицом к хвосту; A в последнем (5), лицом вперёд.
b.position = Position(car_index=4, level=Level.INSIDE, lane=0)
b.direction = Direction.TOWARD_TAIL
a.position = Position(car_index=5, level=Level.INSIDE, lane=0)
a.direction = Direction.TOWARD_LOCOMOTIVE

events = apply_move(state, "A")
for e in events:
    print(e.type, e.data)
print("A:", a.position, "| B:", b.position)