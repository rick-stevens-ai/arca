"""Ensure the repo root is importable so `from tests._helpers import ...` works
regardless of pytest's invocation directory.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
