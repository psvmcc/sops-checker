from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency should be installed
    raise SystemExit("PyYAML is required. Install with `pip install PyYAML`.") from exc

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that all files matched by .sops.yaml creation_rules are SOPS-encrypted."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root directory (default: current directory)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Encrypt unencrypted matched files in-place using sops.",
    )
    return parser.parse_args(argv)


def looks_sops_encrypted(path: Path) -> bool:
    """
    Heuristics:
    - binary: starts with 'sops' magic header
    - text: contains 'sops:' block or ENC[...] tokens
    """
    try:
        with path.open("rb") as fb:
            head = fb.read(4)
            if head == b"sops":
                return True
    except FileNotFoundError:
        return False

    try:
        with path.open("r", encoding="utf-8") as ft:
            content = ft.read()
    except UnicodeDecodeError:
        # binary but no sops header
        return False

    if "\nsops:" in content or content.startswith("sops:"):
        return True
    if "ENC[" in content:
        return True

    return False


def sops_encrypt_in_place(path: Path) -> bool:
    """Run `sops --encrypt --in-place` for given file."""
    try:
        result = subprocess.run(
            ["sops", "--encrypt", "--in-place", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        print(f"{RED}ERROR:{RESET} 'sops' binary not found in PATH.", file=sys.stderr)
        return False

    if result.returncode != 0:
        print(
            f"{RED}ERROR encrypting{RESET} {path} with sops:\n{result.stderr.strip()}",
            file=sys.stderr,
        )
        return False

    return True


def load_creation_rules(config_path: Path) -> List[Tuple[re.Pattern[str], dict]]:
    if not config_path.exists():
        raise FileNotFoundError(f"No .sops.yaml in {config_path.parent}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    rules = [r for r in (cfg.get("creation_rules") or []) if r.get("path_regex")]
    return [(re.compile(r["path_regex"]), r) for r in rules]


def iter_rule_matches(root: Path, compiled_rules: Iterable[Tuple[re.Pattern[str], dict]]):
    skip_dirs = {".git", ".idea", ".venv", ".tox"}

    for dirpath, dirnames, filenames in os.walk(root):
        parts = Path(dirpath).parts
        if any(p in skip_dirs for p in parts):
            continue

        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            rel_path = Path(rel)
            for cregex, rule in compiled_rules:
                if cregex.match(str(rel_path)):
                    yield rel_path
                    break


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    fix = args.fix

    config_path = root / ".sops.yaml"

    try:
        compiled = load_creation_rules(config_path)
    except FileNotFoundError:
        print(f"{RED}No .sops.yaml in {root}{RESET}", file=sys.stderr)
        return 2

    if not compiled:
        print(f"{YELLOW}No creation_rules with path_regex in .sops.yaml{RESET}")
        return 0

    matched: List[Tuple[Path, bool]] = []
    missing: List[Path] = []

    for rel in iter_rule_matches(root, compiled):
        full = root / rel
        is_enc = looks_sops_encrypted(full)
        matched.append((rel, is_enc))
        if not is_enc:
            missing.append(rel)

    if matched:
        print("SOPS rule-matched files:")
        for rel, ok in sorted(matched, key=lambda x: str(x[0])):
            status = f"{GREEN}OK{RESET}" if ok else f"{RED}MISSING_ENCRYPTION{RESET}"
            print(f"  [{status}] {rel}")
    else:
        print(f"{YELLOW}No files matched any .sops.yaml path_regex rules.{RESET}")

    if not missing:
        print(f"\n{GREEN}OK{RESET}: all matched files look SOPS-encrypted.")
        return 0

    if not fix:
        print(
            f"\nRun with {YELLOW}--fix{RESET} to encrypt files marked as {RED}MISSING_ENCRYPTION{RESET} automatically using sops."
        )
        return 1

    print(
        f"\nAttempting to encrypt {len(missing)} file(s) with sops [{YELLOW}--fix{RESET} provided]:"
    )
    still_missing: List[Path] = []

    for rel in missing:
        path = root / rel
        print(f"  -> {CYAN}encrypting{RESET} {rel} ... ", end="")
        ok = sops_encrypt_in_place(path)
        if not ok or not looks_sops_encrypted(path):
            print(f"{RED}FAIL{RESET}")
            still_missing.append(rel)
        else:
            print(f"{GREEN}OK{RESET}")

    if still_missing:
        print(f"\n{RED}Failed to encrypt some files:{RESET}")
        for rel in still_missing:
            print(f"  - {rel}")
        return 1

    print(
        f"\n{GREEN}OK{RESET}: all previously unencrypted matched files have been encrypted with sops."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
