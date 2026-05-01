import json
import subprocess
from pathlib import Path
import pytest
import narrate


def test_build_prompt_includes_delta_and_lang():
    p = narrate.build_prompt(
        delta=[{"role": "user", "text": "do X"}, {"role": "assistant", "text": "did X"}],
        lang="ko",
    )
    assert "do X" in p and "did X" in p
    assert "한국어" in p or "Korean" in p


def test_build_prompt_english_default():
    p = narrate.build_prompt(delta=[{"role": "user", "text": "hi"}], lang="en")
    assert "hi" in p
    assert "English" in p


def test_call_codex_exec_success(tmp_path, monkeypatch):
    out = tmp_path / "out.json"
    expected = {"title": "T", "what_why": "WW", "decisions": [], "open": [], "next": "N"}
    out.write_text(json.dumps(expected))

    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = narrate.call_codex_exec(prompt="x", schema_path=tmp_path / "s.json", out_path=out, timeout=5)
    assert result == expected


def test_call_codex_exec_failure(tmp_path, monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")
    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(narrate.NarrationError, match="codex exec failed"):
        narrate.call_codex_exec(prompt="x", schema_path=tmp_path / "s.json", out_path=tmp_path / "o.json", timeout=5)


def test_call_codex_exec_invalid_json(tmp_path, monkeypatch):
    out = tmp_path / "out.json"
    out.write_text("not json")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "", ""))
    with pytest.raises(narrate.NarrationError, match="invalid JSON"):
        narrate.call_codex_exec(prompt="x", schema_path=tmp_path / "s.json", out_path=out, timeout=5)


def test_validate_required_fields(tmp_path):
    bad = {"title": "T"}
    with pytest.raises(narrate.NarrationError, match="missing required field"):
        narrate.validate(bad)
    good = {"title": "T", "what_why": "W", "decisions": [], "open": [], "next": "N"}
    narrate.validate(good)
