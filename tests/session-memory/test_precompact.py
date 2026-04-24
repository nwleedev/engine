# tests/session-memory/test_precompact.py
import io, json, os, sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import pre_compact as pc


MOCK_NARRATION = json.dumps({
    "result": json.dumps({
        "title": "precompact-saved",
        "narration": "컴팩션 전에 컨텍스트를 저장했습니다."
    })
})


def test_precompact_writes_context_before_compact(tmp_path):
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    payload = json.dumps({"transcript_path": fixture, "session_id": "precompact-write-test"})

    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout=f"{tmp_path}\n"),   # find_project_root
            mock.Mock(returncode=0, stdout=MOCK_NARRATION),    # call_claude_narration
            mock.Mock(returncode=128, stdout=""),               # get_git_commits: git is-inside-work-tree
            mock.Mock(returncode=128, stdout=""),               # get_git_head
        ]
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                pc.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    session_dir = tmp_path / ".claude" / "sessions" / "precompact-write-test"
    contexts = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(contexts) == 1, "CONTEXT file should be created before compaction"
    assert "precompact-saved" in contexts[0].name


def test_precompact_creates_flag_file(tmp_path):
    """Flag file must be created even when delta is empty."""
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    session_id = "flag-test-001"
    payload = json.dumps({"transcript_path": fixture, "session_id": session_id})

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        # Mock extract_delta to return empty so LLM call is skipped
        with mock.patch("handwrite_context.extract_delta", return_value=[]):
            sys.stdin = io.StringIO(payload)
            try:
                pc.main()
            except SystemExit:
                pass
            finally:
                sys.stdin = sys.__stdin__

    flag_path = tmp_path / ".claude" / "sessions" / f"compacted.{session_id}.flag"
    assert flag_path.exists(), "Flag file must be created by pre_compact hook"
    assert flag_path.read_text(encoding="utf-8") == session_id


def test_precompact_outputs_system_message_when_context_exists(tmp_path):
    """systemMessage must be output when context files exist."""
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    session_id = "sysmsg-test-001"
    payload = json.dumps({"transcript_path": fixture, "session_id": session_id})

    # Pre-create a context file so load_recent_context_entries() returns content
    session_dir = tmp_path / ".claude" / "sessions" / session_id
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    (contexts_dir / "CONTEXT-20260424-1200-test-work.md").write_text(
        "## 무엇을 왜\n테스트 작업", encoding="utf-8"
    )

    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        with mock.patch("handwrite_context.extract_delta", return_value=[]):
            sys.stdin = io.StringIO(payload)
            try:
                with mock.patch("sys.stdout", captured):
                    pc.main()
            except SystemExit:
                pass
            finally:
                sys.stdin = sys.__stdin__

    output = captured.getvalue().strip()
    assert output, "systemMessage JSON must be printed when context exists"
    data = json.loads(output)
    assert "systemMessage" in data
    assert "테스트 작업" in data["systemMessage"]


def test_precompact_no_system_message_when_no_context(tmp_path):
    """No output when no context files exist."""
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    session_id = "no-sysmsg-test"
    payload = json.dumps({"transcript_path": fixture, "session_id": session_id})

    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        with mock.patch("handwrite_context.extract_delta", return_value=[]):
            sys.stdin = io.StringIO(payload)
            try:
                with mock.patch("sys.stdout", captured):
                    pc.main()
            except SystemExit:
                pass
            finally:
                sys.stdin = sys.__stdin__

    output = captured.getvalue().strip()
    assert output == "", "No output when no context files exist"


def test_precompact_exits_zero_on_narration_failure(tmp_path):
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    payload = json.dumps({"transcript_path": fixture, "session_id": "precompact-fail-test"})

    exited_with = None
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        with mock.patch("handwrite_context.call_claude_narration", side_effect=Exception("API error")):
            sys.stdin = io.StringIO(payload)
            try:
                pc.main()
            except SystemExit as e:
                exited_with = e.code
            finally:
                sys.stdin = sys.__stdin__

    assert exited_with == 0, "Hook must exit 0 even on narration failure"
    session_dir = tmp_path / ".claude" / "sessions" / "precompact-fail-test"
    contexts_dir = session_dir / "contexts"
    if contexts_dir.exists():
        assert len(list(contexts_dir.glob("CONTEXT-*.md"))) == 0
