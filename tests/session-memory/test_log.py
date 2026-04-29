import json
from pathlib import Path
import log as lg


def test_append_one_line(tmp_path):
    p = tmp_path / "log.jsonl"
    lg.append(p, {"event": "Stop", "decision": "skip"})
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["event"] == "Stop"
    assert "ts" in obj


def test_appends_to_existing(tmp_path):
    p = tmp_path / "log.jsonl"
    lg.append(p, {"event": "a"})
    lg.append(p, {"event": "b"})
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["event"] == "a"
    assert json.loads(lines[1])["event"] == "b"


def test_creates_parent_dir(tmp_path):
    p = tmp_path / "deep" / "nested" / "log.jsonl"
    lg.append(p, {"event": "x"})
    assert p.exists()


def test_silent_failure_on_io_error(tmp_path, monkeypatch):
    bad = Path("/dev/null/cannot/write/here.jsonl")
    lg.append(bad, {"event": "x"})  # no exception expected
