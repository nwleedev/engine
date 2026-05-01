import os
from pathlib import Path
import pytest
import dotenv_loader as dl


def test_loads_nearest_env_into_os_environ(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_PROJECT_DIR", raising=False)
    (tmp_path / ".env").write_text("CODEX_PROJECT_DIR=/abs/foo\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    dl.load_project_dotenv(str(sub))
    assert os.environ["CODEX_PROJECT_DIR"] == "/abs/foo"


def test_no_override_when_already_set(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_PROJECT_DIR", "/from/shell")
    (tmp_path / ".env").write_text("CODEX_PROJECT_DIR=/abs/foo\n")
    dl.load_project_dotenv(str(tmp_path))
    assert os.environ["CODEX_PROJECT_DIR"] == "/from/shell"


def test_walk_up_stops_at_first_env(tmp_path, monkeypatch):
    monkeypatch.delenv("FOO", raising=False)
    (tmp_path / ".env").write_text("FOO=root\n")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    (sub / ".env").write_text("FOO=nearest\n")
    dl.load_project_dotenv(str(sub))
    assert os.environ["FOO"] == "nearest"


def test_stops_at_home_boundary(tmp_path, monkeypatch):
    monkeypatch.delenv("HOMETEST", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / ".env").write_text("HOMETEST=should_not_load\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    dl.load_project_dotenv(str(sub))
    assert "HOMETEST" not in os.environ


def test_parses_quoted_values_and_skips_comments(tmp_path, monkeypatch):
    monkeypatch.delenv("A", raising=False)
    monkeypatch.delenv("B", raising=False)
    (tmp_path / ".env").write_text(
        '# comment\nA="quoted value"\nB=bare # trailing\n'
    )
    dl.load_project_dotenv(str(tmp_path))
    assert os.environ["A"] == "quoted value"
    assert os.environ["B"] == "bare"


def test_no_env_file_is_noop(tmp_path):
    dl.load_project_dotenv(str(tmp_path))
