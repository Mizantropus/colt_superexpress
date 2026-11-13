import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.game.setup import setup_game
from app.game.actions import apply_horse, apply_move
from app.game.models import Action, Direction, Level, Position, Posture

# Сценарий 1: на локомотиве уже стоит A (пришёл перемещением с первого вагона).
state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])
a = state.bandit_by_id("A")
a.position = Position(car_index=1, level=Level.ROOF, lane=0)
a.direction = Direction.TOWARD_LOCOMOTIVE

apply_horse(state, "B")
b = state.bandit_by_id("B")
print("Сценарий 1 (A уже на крыше, B лошадь): A lane =", a.position.lane, ", B lane =", b.position.lane, "(B должен быть больше A = правее)")

# Сценарий 2: две лошади подряд.
state = setup_game([("A", "A"), ("B", "B"), ("C", "C")])
apply_horse(state, "A")
apply_horse(state, "B")
a = state.bandit_by_id("A")
b = state.bandit_by_id("B")
print("Сценарий 2 (A лошадь, потом B лошадь): A lane =", a.position.lane, ", B lane =", b.position.lane, "(B должен быть больше A)")