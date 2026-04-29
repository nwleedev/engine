"""End-to-end: simulate Stop → SessionStart compact → resume cycle without real claude -p."""
import json
from pathlib import Path
from unittest.mock import patch

import narration_pipeline as np
import injection


def _mock_narration(*args, **kwargs):
    class R:
        returncode = 0
        stdout = json.dumps({"result": json.dumps({
            "title": "e2e-task",
            "what_why": "did stuff. for reasons.",
            "decisions": ["chose A"],
            "incomplete": [],
            "next_instructions": "continue.",
        })})
        stderr = ""
    return R()


def test_stop_then_compact_session_start_then_resume(tmp_path, capsys):
    # 1. Stop hook generates narration
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(json.dumps({
        "uuid": "u1", "cwd": str(tmp_path),
        "message": {"role": "user", "content": "x" * 5000}
    }) + "\n", encoding="utf-8")
    payload = {"transcript_path": str(transcript), "session_id": "e2e-1"}

    with patch("subprocess.run", side_effect=_mock_narration):
        np.run("ManualCheckpoint", payload)

    sd = tmp_path / ".claude" / "sessions" / "e2e-1"
    assert (sd / "INDEX.md").exists()
    assert any((sd / "contexts").glob("CONTEXT-*.md"))

    # 2. SessionStart with source=compact returns the recent context
    capsys.readouterr()
    injection.handle({"session_id": "e2e-1", "cwd": str(tmp_path), "source": "compact"})
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert "<session-context>" in obj["hookSpecificOutput"]["additionalContext"]

    # 3. SessionStart with source=resume returns INDEX
    capsys.readouterr()
    injection.handle({"session_id": "e2e-1", "cwd": str(tmp_path), "source": "resume"})
    out = capsys.readouterr().out
    obj = json.loads(out)
    assert "<session-resume>" in obj["hookSpecificOutput"]["additionalContext"]
