#!/usr/bin/env python3
"""Convenience wrapper so the tool can run without installing the package."""

from __future__ import annotations

import pathlib
import sys


def _bootstrap_src_on_path() -> None:
    project_root = pathlib.Path(__file__).resolve().parent
    src_dir = project_root / "src"
    if src_dir.is_dir():
        sys.path.insert(0, str(src_dir))


def main() -> int:
    _bootstrap_src_on_path()
    from sops_checker.cli import main as pkg_main

    return pkg_main()


if __name__ == "__main__":
    raise SystemExit(main())
