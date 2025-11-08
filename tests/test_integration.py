from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
import re

import pytest

pytest.importorskip("yaml")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
FIXTURE_REPO = PROJECT_ROOT / "tests" / "fixtures" / "repo"


@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    shutil.copytree(FIXTURE_REPO, dest)
    return dest


def prepare_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    src_path = str(SRC_DIR)
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing}" if existing else src_path
    if extra:
        env.update(extra)
    return env


ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def run_cli(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full_env = prepare_env(env)
    completed = subprocess.run(
        [sys.executable, "-m", "sops_checker", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=full_env,
    )
    return completed


def test_cli_reports_missing_when_run_as_module(fixture_repo: Path) -> None:
    completed = run_cli([], cwd=fixture_repo)
    clean_output = ANSI_PATTERN.sub("", completed.stdout)

    assert completed.returncode == 1
    assert "[MISSING_ENCRYPTION] secrets/plain.yaml" in clean_output
    assert "secrets/encrypted.yaml" in clean_output


def test_cli_marks_encrypted_files_ok(fixture_repo: Path) -> None:
    completed = run_cli([], cwd=fixture_repo)
    clean_output = ANSI_PATTERN.sub("", completed.stdout)
    lines = [line.strip() for line in clean_output.splitlines() if "secrets/encrypted.yaml" in line]

    assert lines, f"No line mentioning encrypted.yaml found:\n{clean_output}"
    assert any("[OK]" in line for line in lines)
    assert all("[MISSING_ENCRYPTION]" not in line for line in lines)


def test_cli_fix_mode_with_fake_sops(fixture_repo: Path, monkeypatch) -> None:
    target = fixture_repo / "secrets" / "plain.yaml"
    # Create a fake sops executable that writes the magic header when called.
    bin_dir = fixture_repo / "bin"
    bin_dir.mkdir()
    fake_sops = bin_dir / "sops"
    fake_sops.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env python3
            import pathlib
            import sys

            path = pathlib.Path(sys.argv[-1])
            path.write_bytes(b"sops" + path.read_bytes())
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    fake_sops.chmod(0o755)

    env = {"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"}

    completed = run_cli(["--fix"], cwd=fixture_repo, env=env)

    assert completed.returncode == 0
    assert "encrypting" in completed.stdout
    assert target.read_bytes().startswith(b"sops")
