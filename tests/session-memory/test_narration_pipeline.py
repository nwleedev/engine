import json
from pathlib import Path
from unittest.mock import patch
import narration_pipeline as np


def _mock_narration_success(*args, **kwargs):
    class R:
        returncode = 0
        stdout = json.dumps({"result": json.dumps({
            "title": "test-title",
            "what_why": "did something. for reason.",
            "decisions": ["chose X over Y"],
            "incomplete": [],
            "next_instructions": "continue.",
        })})
        stderr = ""
    return R()


def _mock_narration_failure(*args, **kwargs):
    class R:
        returncode = 1
        stdout = ""
        stderr = "boom"
    return R()


def _make_payload(tmp_path: Path) -> dict:
    transcript = tmp_path / "transcript.jsonl"
    lines = [
        json.dumps({"uuid": "u1", "cwd": str(tmp_path), "message": {"role": "user", "content": "hi" * 1000}}),
        json.dumps({"uuid": "u2", "message": {"role": "assistant", "content": "ok " * 1000}}),
    ]
    transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"transcript_path": str(transcript), "session_id": "test-session"}


def test_skips_when_below_min_delta(tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(json.dumps({"uuid": "u", "cwd": str(tmp_path), "message": {"role": "user", "content": "ok"}}) + "\n", encoding="utf-8")
    payload = {"transcript_path": str(transcript), "session_id": "s1"}
    with patch("subprocess.run", side_effect=_mock_narration_success) as run:
        np.run("Stop", payload)
    narration_calls = [c for c in run.call_args_list if c[0][0][0] == "claude"]
    assert len(narration_calls) == 0


def test_narrates_and_writes_index_when_passes_gate(tmp_path):
    payload = _make_payload(tmp_path)
    with patch("subprocess.run", side_effect=_mock_narration_success):
        np.run("ManualCheckpoint", payload)
    session_dir = Path(tmp_path) / ".claude" / "sessions" / "test-session"
    assert (session_dir / "INDEX.md").exists()
    contexts = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(contexts) == 1


def test_logs_decision_to_jsonl(tmp_path):
    payload = _make_payload(tmp_path)
    with patch("subprocess.run", side_effect=_mock_narration_success):
        np.run("ManualCheckpoint", payload)
    log_path = Path(tmp_path) / ".claude" / "sessions" / "test-session" / "log.jsonl"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    decisions = [json.loads(l) for l in lines]
    assert any(d.get("decision") == "narrate" for d in decisions)


def test_increments_failure_count_on_subprocess_error(tmp_path):
    payload = _make_payload(tmp_path)
    with patch("subprocess.run", side_effect=_mock_narration_failure):
        np.run("ManualCheckpoint", payload)
    import narration_state
    sd = Path(tmp_path) / ".claude" / "sessions" / "test-session"
    assert narration_state.get_consecutive_failures(sd) == 1


def test_resets_failure_count_on_success(tmp_path):
    import narration_state
    payload = _make_payload(tmp_path)
    sd_path = Path(tmp_path) / ".claude" / "sessions" / "test-session"
    sd_path.mkdir(parents=True)
    narration_state.increment_failures(sd_path)
    assert narration_state.get_consecutive_failures(sd_path) == 1
    with patch("subprocess.run", side_effect=_mock_narration_success):
        np.run("ManualCheckpoint", payload)
    assert narration_state.get_consecutive_failures(sd_path) == 0
