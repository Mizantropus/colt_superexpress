import importlib
import sys
import types
from contextlib import contextmanager
from pathlib import Path

# Шим pytest (офлайн: pytest не установлен)
pytest_mod = types.ModuleType("pytest")

@contextmanager
def _raises(exc_type):
    try:
        yield
    except exc_type:
        return
    except Exception as e:
        raise AssertionError(f"ожидалось {exc_type.__name__}, получено {type(e).__name__}: {e}")
    raise AssertionError(f"ожидалось {exc_type.__name__}, но ничего не выброшено")

pytest_mod.raises = _raises
sys.modules["pytest"] = pytest_mod

BASE = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tests"))

passed = 0
failed = []
skipped = []

for test_file in sorted((BASE / "tests").glob("test_*.py")):
    name = test_file.stem
    if name == "test_health":   # нужен fastapi
        skipped.append(name)
        continue
    try:
        mod = importlib.import_module(name)
    except Exception as e:
        failed.append((name, "(import)", repr(e)))
        continue
    for attr in dir(mod):
        if attr.startswith("test_"):
            fn = getattr(mod, attr)
            if callable(fn):
                try:
                    fn()
                    passed += 1
                except Exception as e:
                    failed.append((name, attr, repr(e)))

print(f"PASSED: {passed}")
print(f"FAILED: {len(failed)}")
print(f"SKIPPED: {skipped}")
for name, attr, err in failed:
    print(f"  FAIL {name}.{attr}: {err}")
sys.exit(1 if failed else 0)