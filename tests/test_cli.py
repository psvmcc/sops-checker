from __future__ import annotations

from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from sops_checker import cli


def write_config(tmp_path: Path, pattern: str = r"^secret\.yaml$") -> None:
    cfg = (
        "creation_rules:\n"
        f"  - path_regex: '{pattern}'\n"
    )
    (tmp_path / ".sops.yaml").write_text(cfg, encoding="utf-8")


def test_exits_when_no_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli.main([str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "No .sops.yaml" in captured.err


def test_ok_when_files_encrypted(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_config(tmp_path)
    (tmp_path / "secret.yaml").write_text("sops:\n  version: 3.7.1\n", encoding="utf-8")

    code = cli.main([str(tmp_path)])

    output = capsys.readouterr().out
    assert code == 0
    assert "OK" in output


def test_reports_missing_encryption(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_config(tmp_path)
    (tmp_path / "secret.yaml").write_text("plain: text\n", encoding="utf-8")

    code = cli.main([str(tmp_path)])

    output = capsys.readouterr().out
    assert code == 1
    assert "MISSING_ENCRYPTION" in output


def test_fix_mode_encrypts_files(tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]) -> None:
    write_config(tmp_path)
    target = tmp_path / "secret.yaml"
    target.write_text("plain: text\n", encoding="utf-8")

    encrypted: dict[str, bool] = {}

    def fake_looks(path: Path) -> bool:
        return encrypted.get(str(path), False)

    def fake_encrypt(path: Path) -> bool:
        encrypted[str(path)] = True
        return True

    monkeypatch.setattr(cli, "looks_sops_encrypted", fake_looks)
    monkeypatch.setattr(cli, "sops_encrypt_in_place", fake_encrypt)

    code = cli.main([str(tmp_path), "--fix"])
    output = capsys.readouterr().out

    assert code == 0
    assert "encrypting" in output
    assert encrypted[str(target)]


def test_binary_magic_header_detected(tmp_path: Path) -> None:
    binary_file = tmp_path / "secret.bin"
    binary_file.write_bytes(b"sops" + b"\x00" * 10)

    assert cli.looks_sops_encrypted(binary_file) is True


def test_text_enc_token_detected(tmp_path: Path) -> None:
    text_file = tmp_path / "secret.yaml"
    text_file.write_text("foo: ENC[AES256_GCM,data:abcd]", encoding="utf-8")

    assert cli.looks_sops_encrypted(text_file) is True


def test_main_handles_empty_rules(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".sops.yaml").write_text("creation_rules: []\n", encoding="utf-8")

    code = cli.main([str(tmp_path)])
    output = capsys.readouterr().out

    assert code == 0
    assert "No creation_rules" in output


def test_iter_rule_matches_skips_hidden_dirs(tmp_path: Path) -> None:
    files_dir = tmp_path / "configs"
    files_dir.mkdir()
    legit = files_dir / "secret.yaml"
    legit.write_text("sops:\n", encoding="utf-8")

    ignored_dir = tmp_path / ".git"
    ignored_dir.mkdir()
    (ignored_dir / "secret.yaml").write_text("plain\n", encoding="utf-8")

    compiled = [(re.compile(r".*secret\.yaml$"), {})]
    matches = list(cli.iter_rule_matches(tmp_path, compiled))

    assert Path("configs/secret.yaml") in matches
    assert all(".git" not in str(match) for match in matches)


def test_sops_encrypt_handles_missing_binary(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "secret.yaml"

    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    assert cli.sops_encrypt_in_place(path) is False


def test_sops_encrypt_handles_failure(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "secret.yaml"

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=1, stderr="boom", stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    assert cli.sops_encrypt_in_place(path) is False


def test_sops_encrypt_success(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "secret.yaml"

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    assert cli.sops_encrypt_in_place(path) is True
