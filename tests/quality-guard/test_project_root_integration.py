# tests/quality-guard/test_project_root_integration.py
"""Integration tests: find_project_root is used at each quality-guard call site."""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import user_prompt_handler as uph
import superficial_detector as sd


# ---------------------------------------------------------------------------
# user_prompt_handler: project root resolved from monorepo sub-directory
# ---------------------------------------------------------------------------

def test_user_prompt_handler_resolves_root_via_env_var(tmp_path, monkeypatch):
    """CLAUDE_PROJECT_DIR wins over payload cwd for index lookup."""
    root = tmp_path / "monorepo"
    root.mkdir()
    sub = root / "packages" / "api"
    sub.mkdir(parents=True)

    # Place INDEX.md under the monorepo root, not under the sub-dir.
    index = root / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True)
    index.write_text("| Pytest | .claude/refs/pytest.md | python |", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))

    f = io.StringIO()
    with redirect_stdout(f):
        # payload cwd points at a sub-directory — without root resolution
        # read_index would return "" and debiasing fallback would be used.
        uph.main_with_payload({"prompt": "Write a test", "cwd": str(sub)})

    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<quality-instruction>" in context, (
        "Expected quality-instruction because INDEX.md lives at the resolved root"
    )


def test_user_prompt_handler_resolves_root_via_topmost_claude(tmp_path, monkeypatch):
    """Topmost .claude/ ancestor is used when env var is absent."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)

    # .claude/ at the outer level only
    (outer / ".claude").mkdir()
    index = outer / ".claude" / "refs" / "INDEX.md"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text("| Requests | .claude/refs/requests.md | http |", encoding="utf-8")

    f = io.StringIO()
    with redirect_stdout(f):
        uph.main_with_payload({"prompt": "Fetch a URL", "cwd": str(inner)})

    output = json.loads(f.getvalue())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "<quality-instruction>" in context, (
        "Expected quality-instruction because INDEX.md lives at the topmost .claude root"
    )


# ---------------------------------------------------------------------------
# superficial_detector: project root resolved for feedback writes
# ---------------------------------------------------------------------------

def test_superficial_detector_writes_to_resolved_root(tmp_path, monkeypatch):
    """Feedback files are anchored at the resolved project root, not payload cwd."""
    root = tmp_path / "repo"
    root.mkdir()
    sub = root / "services" / "api"
    sub.mkdir(parents=True)

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))

    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: silences exception\nCONFIDENCE: high"

    err = io.StringIO()
    sd.main_with_payload(
        {
            "cwd": str(sub),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "def f(): broken()",
                "new_string": "def f():\n    try:\n        broken()\n    except:\n        pass",
            },
        },
        llm_fn=fake_llm,
    )

    # Feedback must land under the resolved root, not under sub.
    raw_at_root = root / ".claude" / "feedback" / "raw.md"
    raw_at_sub = sub / ".claude" / "feedback" / "raw.md"
    assert raw_at_root.exists(), "raw.md must be written at the resolved project root"
    assert not raw_at_sub.exists(), "raw.md must NOT be written under the payload cwd sub-directory"
