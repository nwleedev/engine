import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-builder/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import harness_audit as sh


def _make_transcript(tmp_path: Path, tool_calls: list[dict]) -> str:
    """Write a minimal JSONL transcript with tool_use blocks."""
    lines = []
    for tc in tool_calls:
        entry = {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": tc["name"],
                        "input": {"file_path": tc["file_path"]},
                    }
                ],
            }
        }
        lines.append(json.dumps(entry))
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def test_extracts_write_tool_calls(tmp_path):
    transcript = _make_transcript(tmp_path, [{"name": "Write", "file_path": "src/foo.ts"}])
    files = sh.extract_written_files(transcript)
    assert "src/foo.ts" in files


def test_extracts_edit_tool_calls(tmp_path):
    transcript = _make_transcript(tmp_path, [{"name": "Edit", "file_path": "src/bar.tsx"}])
    files = sh.extract_written_files(transcript)
    assert "src/bar.tsx" in files


def test_ignores_read_tool_calls(tmp_path):
    transcript = _make_transcript(tmp_path, [{"name": "Read", "file_path": "src/foo.ts"}])
    files = sh.extract_written_files(transcript)
    assert files == []


def test_deduplicates_paths(tmp_path):
    transcript = _make_transcript(tmp_path, [
        {"name": "Write", "file_path": "src/foo.ts"},
        {"name": "Edit", "file_path": "src/foo.ts"},
    ])
    files = sh.extract_written_files(transcript)
    assert files.count("src/foo.ts") == 1


def test_empty_transcript_returns_empty(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert sh.extract_written_files(str(path)) == []


def test_missing_transcript_returns_empty():
    assert sh.extract_written_files("/nonexistent/path.jsonl") == []


def test_no_harness_produces_no_output(tmp_path):
    transcript = _make_transcript(tmp_path, [{"name": "Write", "file_path": "src/foo.ts"}])
    f = io.StringIO()
    with redirect_stdout(f):
        sh.main_with_payload({"cwd": str(tmp_path), "transcript_path": transcript})
    assert f.getvalue() == ""


def test_harness_present_outputs_reminder(tmp_path):
    (tmp_path / ".claude" / "harness").mkdir(parents=True)
    (tmp_path / ".claude" / "harness" / "test.md").write_text("# Test\n")
    transcript = _make_transcript(tmp_path, [{"name": "Write", "file_path": "src/foo.ts"}])
    f = io.StringIO()
    with redirect_stdout(f):
        sh.main_with_payload({"cwd": str(tmp_path), "transcript_path": transcript})
    output = json.loads(f.getvalue())
    assert "src/foo.ts" in output["systemMessage"]


def test_no_written_files_produces_no_output(tmp_path):
    (tmp_path / ".claude" / "harness").mkdir(parents=True)
    transcript = _make_transcript(tmp_path, [])
    f = io.StringIO()
    with redirect_stdout(f):
        sh.main_with_payload({"cwd": str(tmp_path), "transcript_path": transcript})
    assert f.getvalue() == ""


def test_output_uses_system_message_and_continue(tmp_path):
    (tmp_path / ".claude" / "harness").mkdir(parents=True)
    (tmp_path / ".claude" / "harness" / "test.md").write_text("# Test\n")
    transcript = _make_transcript(tmp_path, [{"name": "Write", "file_path": "src/foo.ts"}])
    f = io.StringIO()
    with redirect_stdout(f):
        sh.main_with_payload({"cwd": str(tmp_path), "transcript_path": transcript})
    output = json.loads(f.getvalue())
    assert output.get("continue") is True
    assert "systemMessage" in output


def test_invalid_payload_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        sh.main_with_payload("not-a-dict")
    assert f.getvalue() == ""
