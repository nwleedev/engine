import json
from pathlib import Path

import injection as inj


def test_startup_returns_insight_only(tmp_path, capsys):
    insight = tmp_path / ".claude" / "INSIGHT.md"
    insight.parent.mkdir(parents=True)
    insight.write_text("\n---\n**2026-04-29** · `abc12345`\n\nfact one\n", encoding="utf-8")
    payload = {"session_id": "new-id", "cwd": str(tmp_path), "source": "startup"}
    inj.handle(payload)
    out = capsys.readouterr().out
    obj = json.loads(out)
    text = obj["hookSpecificOutput"]["additionalContext"]
    assert "fact one" in text
    assert "<codebase-insights>" in text


def test_compact_returns_recent_contexts(tmp_path, capsys):
    sd = tmp_path / ".claude" / "sessions" / "id1"
    contexts = sd / "contexts"
    contexts.mkdir(parents=True)
    (contexts / "CONTEXT-20260429-1300-a.md").write_text("alpha body", encoding="utf-8")
    (contexts / "CONTEXT-20260429-1400-b.md").write_text("beta body", encoding="utf-8")
    (sd / "INDEX.md").write_text("---\nsession_id: id1\n---\n", encoding="utf-8")
    payload = {"session_id": "id1", "cwd": str(tmp_path), "source": "compact"}
    inj.handle(payload)
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert "alpha body" in obj["hookSpecificOutput"]["additionalContext"] or \
           "beta body" in obj["hookSpecificOutput"]["additionalContext"]


def test_clear_outputs_nothing(tmp_path, capsys):
    payload = {"session_id": "id1", "cwd": str(tmp_path), "source": "clear"}
    inj.handle(payload)
    assert capsys.readouterr().out.strip() == ""


def test_resume_returns_index(tmp_path, capsys):
    sd = tmp_path / ".claude" / "sessions" / "id1"
    sd.mkdir(parents=True)
    (sd / "INDEX.md").write_text("---\nsession_id: id1\n---\n# summary\n", encoding="utf-8")
    payload = {"session_id": "id1", "cwd": str(tmp_path), "source": "resume"}
    inj.handle(payload)
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert "summary" in obj["hookSpecificOutput"]["additionalContext"]


def test_respects_8kb_budget(tmp_path, capsys):
    insight = tmp_path / ".claude" / "INSIGHT.md"
    insight.parent.mkdir(parents=True)
    insight.write_text("x" * 50_000, encoding="utf-8")
    payload = {"session_id": "id1", "cwd": str(tmp_path), "source": "startup"}
    inj.handle(payload)
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert len(obj["hookSpecificOutput"]["additionalContext"]) <= 8_500
