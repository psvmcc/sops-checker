"""Utilities for checking SOPS-encrypted files defined via .sops.yaml."""

from importlib import metadata

from .cli import main

try:
    __version__ = metadata.version("sops-checker")
except metadata.PackageNotFoundError:  # pragma: no cover - during local dev
    __version__ = "0.0.0"

__all__ = ["main", "__version__"]
