import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/ref-manager/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import session_start_handler as ssh
import ref_discovery as rd


# ── build_refs_context ────────────────────────────────────────────────────────

def test_build_refs_context_no_entries_returns_empty(tmp_path):
    assert ssh.build_refs_context(str(tmp_path)) == ""


def test_build_refs_context_injects_table(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| python-typing | .claude/refs/typing/typing.md | python, typing |\n",
        encoding="utf-8",
    )
    context = ssh.build_refs_context(str(tmp_path))
    assert "python-typing" in context
    assert ".claude/refs/typing/typing.md" in context
    assert "python, typing" in context


def test_build_refs_context_includes_header_instruction(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| my-ref | .claude/refs/topic/doc.md |  |\n",
        encoding="utf-8",
    )
    context = ssh.build_refs_context(str(tmp_path))
    assert "available-refs" in context
    assert "Read tool" in context


def test_build_refs_context_empty_tags_row(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| no-tags | .claude/refs/t/file.md |  |\n",
        encoding="utf-8",
    )
    context = ssh.build_refs_context(str(tmp_path))
    assert "no-tags" in context


# ── main ─────────────────────────────────────────────────────────────────────

def test_main_no_refs_produces_no_output(tmp_path):
    payload = json.dumps({"cwd": str(tmp_path)})
    buf = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)):
        with redirect_stdout(buf):
            ssh.main()
    assert buf.getvalue().strip() == ""


def test_main_with_refs_produces_json(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| api-spec | .claude/refs/api/spec.md | api |\n",
        encoding="utf-8",
    )
    payload = json.dumps({"cwd": str(tmp_path)})
    buf = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)):
        with redirect_stdout(buf):
            ssh.main()
    output = json.loads(buf.getvalue().strip())
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "api-spec" in output["hookSpecificOutput"]["additionalContext"]


def test_main_uses_claude_project_dir_fallback(tmp_path, monkeypatch):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| fallback-ref | .claude/refs/fb/doc.md |  |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    # Pass empty cwd so fallback to env var is exercised
    payload = json.dumps({"cwd": ""})
    buf = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)):
        with redirect_stdout(buf):
            ssh.main()
    output = json.loads(buf.getvalue().strip())
    assert "fallback-ref" in output["hookSpecificOutput"]["additionalContext"]


def test_main_invalid_json_stdin_is_noop(tmp_path):
    buf = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO("not json")):
        with redirect_stdout(buf):
            ssh.main()
    assert buf.getvalue().strip() == ""


# ── ref_discovery.has_refs ────────────────────────────────────────────────────

def test_has_refs_returns_false_when_no_index(tmp_path):
    assert rd.has_refs(str(tmp_path)) is False


def test_has_refs_returns_false_when_index_has_no_entries(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n",
        encoding="utf-8",
    )
    assert rd.has_refs(str(tmp_path)) is False


def test_has_refs_returns_true_when_entries_exist(tmp_path):
    refs_dir = tmp_path / ".claude" / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "INDEX.md").write_text(
        "# Refs Index\n\n| Name | Path | Tags |\n|---|---|---|\n"
        "| some-ref | .claude/refs/t/doc.md |  |\n",
        encoding="utf-8",
    )
    assert rd.has_refs(str(tmp_path)) is True
