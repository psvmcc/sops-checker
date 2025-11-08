"""Test helpers."""

from __future__ import annotations

import pathlib
import sys


def pytest_configure():
    """Ensure the src/ directory is importable when running tests locally."""
    project_root = pathlib.Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"
    if src_dir.is_dir() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
