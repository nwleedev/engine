# tests/quality-guard/test_stop_resolution.py
"""Integration tests: stop.py resolves project root before writing feedback files."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import quality_analyzer as qa


def _make_transcript(tmp_path: Path) -> Path:
    transcript = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps({
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": "Explain caching"}]},
        }),
        json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "Caching is great. " * 20}]},
        }),
    ]
    transcript.write_text("\n".join(lines), encoding="utf-8")
    return transcript


def _mock_subprocess_result() -> MagicMock:
    result = MagicMock()
    result.returncode = 0
    result.stdout = json.dumps({"result": json.dumps([
        {"index": 0, "reason": "vague enumeration", "confidence": "high"},
    ])})
    return result


# ---------------------------------------------------------------------------
# CLAUDE_PROJECT_DIR wins over payload cwd for output file placement
# ---------------------------------------------------------------------------

def test_stop_writes_feedback_to_env_declared_root(tmp_path, monkeypatch):
    """raw.md and pending_review.txt must be written at the resolved root."""
    root = tmp_path / "monorepo"
    root.mkdir()
    sub = root / "packages" / "api"
    sub.mkdir(parents=True)

    transcript = _make_transcript(sub)

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    monkeypatch.delenv("CLAUDE_WRITING_CONTEXT", raising=False)

    payload = {"cwd": str(sub), "transcript_path": str(transcript)}

    from project_root import find_project_root
    resolved_cwd = find_project_root(str(sub))

    with patch("quality_analyzer.subprocess.run", return_value=_mock_subprocess_result()):
        qa.run_quality_analysis(payload, resolved_cwd)

    raw_at_root = root / ".claude" / "feedback" / "raw.md"
    raw_at_sub = sub / ".claude" / "feedback" / "raw.md"
    assert raw_at_root.exists(), "raw.md must be written at the resolved project root"
    assert not raw_at_sub.exists(), "raw.md must NOT be written under the payload cwd sub-directory"

    pending_at_root = root / ".claude" / "quality" / "pending_review.txt"
    assert pending_at_root.exists(), "pending_review.txt must be written at the resolved project root"
    assert pending_at_root.read_text(encoding="utf-8").strip() == "1"


def test_stop_writes_feedback_to_topmost_claude_root(tmp_path, monkeypatch):
    """When env var is absent, topmost .claude/ ancestor is used."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_WRITING_CONTEXT", raising=False)

    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    (outer / ".claude").mkdir()

    transcript = _make_transcript(inner)

    payload = {"cwd": str(inner), "transcript_path": str(transcript)}

    from project_root import find_project_root
    resolved_cwd = find_project_root(str(inner))

    with patch("quality_analyzer.subprocess.run", return_value=_mock_subprocess_result()):
        qa.run_quality_analysis(payload, resolved_cwd)

    raw_at_outer = outer / ".claude" / "feedback" / "raw.md"
    raw_at_inner = inner / ".claude" / "feedback" / "raw.md"
    assert raw_at_outer.exists(), "raw.md must be written at the topmost .claude root"
    assert not raw_at_inner.exists(), "raw.md must NOT be written under the inner sub-directory"


def test_stop_env_var_takes_priority_over_topmost_claude(tmp_path, monkeypatch):
    """CLAUDE_PROJECT_DIR is used even when a .claude/ directory exists in the cwd ancestors."""
    declared_root = tmp_path / "declared"
    declared_root.mkdir()

    repo = tmp_path / "repo"
    sub = repo / "pkg"
    sub.mkdir(parents=True)
    (repo / ".claude").mkdir()  # topmost .claude ancestor would resolve to repo

    transcript = _make_transcript(sub)

    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(declared_root))
    monkeypatch.delenv("CLAUDE_WRITING_CONTEXT", raising=False)

    payload = {"cwd": str(sub), "transcript_path": str(transcript)}

    from project_root import find_project_root
    resolved_cwd = find_project_root(str(sub))

    with patch("quality_analyzer.subprocess.run", return_value=_mock_subprocess_result()):
        qa.run_quality_analysis(payload, resolved_cwd)

    raw_at_declared = declared_root / ".claude" / "feedback" / "raw.md"
    raw_at_repo = repo / ".claude" / "feedback" / "raw.md"
    assert raw_at_declared.exists(), "raw.md must be written at the CLAUDE_PROJECT_DIR root"
    assert not raw_at_repo.exists(), "raw.md must NOT be written at the .claude/ ancestor"
