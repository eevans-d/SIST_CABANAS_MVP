# Reexport fixtures desde tests/ para que tests_e2e los vea
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tests_dir = root / "tests"
if str(tests_dir) not in sys.path:
	sys.path.insert(0, str(tests_dir))

from conftest import *  # type: ignore  # noqa: F401,F403
