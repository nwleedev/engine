import json, os, sys, io
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import handwrite_context as hw


# ── helpers ──────────────────────────────────────────────────────────

def make_insight_file(path: Path, entries: list[str]) -> None:
    """Write INSIGHT.md using the same format as append_insights_to_project()."""
    content = ""
    for entry in entries:
        content += f"\n---\n**2026-04-01 00:00** · `abc12345`\n\n{entry}\n"
    path.write_text(content, encoding="utf-8")


# ── load_recent_insights ─────────────────────────────────────────────

def test_load_insights_missing_file(tmp_path):
    assert hw.load_recent_insights(str(tmp_path)) == ""


def test_load_insights_empty_file(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "INSIGHT.md").write_text("", encoding="utf-8")
    assert hw.load_recent_insights(str(tmp_path)) == ""


def test_load_insights_fewer_than_max(tmp_path):
    (tmp_path / ".claude").mkdir()
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", ["A", "B", "C"])
    result = hw.load_recent_insights(str(tmp_path), max_entries=20)
    assert "A" in result
    assert "B" in result
    assert "C" in result


def test_load_insights_truncates_to_max(tmp_path):
    (tmp_path / ".claude").mkdir()
    entries = [f"insight-{i}" for i in range(30)]
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", entries)
    result = hw.load_recent_insights(str(tmp_path), max_entries=20)
    assert "insight-0" not in result   # oldest dropped
    assert "insight-29" in result      # newest kept


def test_load_insights_preserves_exact_content(tmp_path):
    (tmp_path / ".claude").mkdir()
    code_insight = "`datetime.utcnow()` → `datetime.now(timezone.utc)` + `.replace(tzinfo=None)`"
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", [code_insight])
    result = hw.load_recent_insights(str(tmp_path))
    assert code_insight in result


# ── inject_insight.main() ─────────────────────────────────────────────
import inject_insight as ii


def test_resolve_cwd_from_payload():
    assert ii.resolve_cwd({"cwd": "/a/b"}) == "/a/b"


def test_resolve_cwd_from_env():
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/env/proj"}, clear=False):
        assert ii.resolve_cwd({}) == "/env/proj"


def test_resolve_cwd_from_pwd():
    # CLAUDE_PROJECT_DIR must be absent for PWD fallback to be reached
    with mock.patch.dict(os.environ, {"PWD": "/pwd/proj"}, clear=True):
        assert ii.resolve_cwd({}) == "/pwd/proj"


def test_resolve_cwd_returns_empty_on_bad_payload():
    assert ii.resolve_cwd("not-a-dict") == ""


def test_inject_outputs_valid_json(tmp_path):
    (tmp_path / ".claude").mkdir()
    make_insight_file(tmp_path / ".claude" / "INSIGHT.md", ["test insight content"])

    payload = json.dumps({"cwd": str(tmp_path), "session_id": "abc"})
    captured = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)), \
         mock.patch("sys.stdout", captured), \
         mock.patch("inject_insight.hw.find_project_root", return_value=str(tmp_path)):
        ii.main()

    out = json.loads(captured.getvalue())
    hook = out["hookSpecificOutput"]
    assert hook["hookEventName"] == "SessionStart"
    ctx = hook["additionalContext"]
    assert ctx.startswith("<codebase-insights>")
    assert ctx.endswith("</codebase-insights>")
    assert "test insight content" in ctx


def test_inject_exits_silently_when_no_file(tmp_path):
    payload = json.dumps({"cwd": str(tmp_path), "session_id": "abc"})
    with mock.patch("sys.stdin", io.StringIO(payload)):
        try:
            ii.main()
            exited = False
            exit_code = None
        except SystemExit as e:
            exited = True
            exit_code = e.code
    assert exited, "main() must call sys.exit(0) when INSIGHT.md does not exist"
    assert exit_code == 0


def test_inject_exits_on_invalid_json():
    with mock.patch("sys.stdin", io.StringIO("not json")):
        try:
            ii.main()
            exited = False
            exit_code = None
        except SystemExit as e:
            exited = True
            exit_code = e.code
    assert exited
    assert exit_code == 0
