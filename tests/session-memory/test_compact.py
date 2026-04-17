import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import compact_handler as ch
import handwrite_context as hw


def test_read_tail_lines_returns_last_n(tmp_path):
    f = tmp_path / "t.jsonl"
    lines = [f"line-{i}" for i in range(200)]
    f.write_text("\n".join(lines))
    result = ch.read_tail_lines(str(f), n=50)
    assert len(result) == 50
    assert result[-1] == "line-199"
    assert result[0] == "line-150"


def test_read_tail_lines_small_file(tmp_path):
    f = tmp_path / "t.jsonl"
    f.write_text("line-0\nline-1\nline-2")
    result = ch.read_tail_lines(str(f), n=100)
    assert result == ["line-0", "line-1", "line-2"]


def test_find_unhandled_compact_detects_new():
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    result = ch.find_unhandled_compact(fixture, "")
    assert result is not None
    assert result["uuid"] == "compact-uuid-001"
    assert result["subtype"] == "compact_boundary"


def test_find_unhandled_compact_skips_handled():
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    result = ch.find_unhandled_compact(fixture, "compact-uuid-001")
    assert result is None


def test_find_unhandled_compact_returns_none_when_absent():
    fixture = str(FIXTURES_DIR / "sample_transcript.jsonl")  # no compact_boundary
    result = ch.find_unhandled_compact(fixture, "")
    assert result is None


def test_find_unhandled_compact_returns_none_on_missing_file():
    result = ch.find_unhandled_compact("/nonexistent/path.jsonl", "")
    assert result is None


def test_should_checkpoint_triggers_on_large_delta():
    result = ch.should_checkpoint({}, "x" * 80_000)
    assert result is True


def test_should_checkpoint_false_on_small_delta_no_timestamp():
    result = ch.should_checkpoint({}, "small")
    assert result is False


def test_should_checkpoint_triggers_on_elapsed_time():
    old_time = (datetime.utcnow() - timedelta(seconds=301)).strftime("%Y-%m-%dT%H:%M:%S")
    result = ch.should_checkpoint({"last_context_written_at": old_time}, "small")
    assert result is True


def test_should_checkpoint_false_when_recent():
    recent = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    result = ch.should_checkpoint({"last_context_written_at": recent}, "small")
    assert result is False


def test_build_compact_context_returns_empty_when_no_dir(tmp_path):
    result = ch.build_compact_context(tmp_path / "no-session", "sess-abc")
    assert result == ""


def test_build_compact_context_returns_empty_when_no_context_files(tmp_path):
    session_dir = tmp_path / "sess"
    (session_dir / "contexts").mkdir(parents=True)
    result = ch.build_compact_context(session_dir, "sess-abc")
    assert result == ""


def test_build_compact_context_includes_session_id(tmp_path):
    session_dir = tmp_path / "sess"
    (session_dir / "contexts").mkdir(parents=True)
    ctx = session_dir / "contexts" / "CONTEXT-0001-api-setup.md"
    ctx.write_text("# CONTEXT-0001: api-setup\n\nAPI를 구현했습니다.\n")
    result = ch.build_compact_context(session_dir, "sess-abc123")
    assert "sess-abc1..." in result
    assert "현재 세션 컨텍스트" in result
    assert "API를 구현했습니다." in result


def test_build_compact_context_latest_3_files(tmp_path):
    session_dir = tmp_path / "sess"
    (session_dir / "contexts").mkdir(parents=True)
    for i in range(1, 6):
        ctx = session_dir / "contexts" / f"CONTEXT-{i:04d}-task-{i}.md"
        ctx.write_text(f"# CONTEXT-{i:04d}\n\n작업 {i} 완료\n")
    result = ch.build_compact_context(session_dir, "sess-xyz")
    assert "작업 5 완료" in result
    assert "작업 4 완료" in result
    assert "작업 3 완료" in result
    assert "작업 1 완료" not in result
    assert "작업 2 완료" not in result


MOCK_NARRATION = json.dumps({
    "result": json.dumps({
        "title": "api-setup",
        "narration": "API 기본 구조를 구현했습니다. 인증 미들웨어는 아직 미완료입니다."
    })
})


def test_main_exits_on_recursive_guard():
    with mock.patch.dict(os.environ, {"CLAUDE_WRITING_CONTEXT": "1"}):
        with mock.patch("sys.exit", side_effect=SystemExit(0)) as mock_exit:
            try:
                ch.main()
            except SystemExit:
                pass
            mock_exit.assert_called_with(0)


def test_main_exits_silently_when_no_compact(tmp_path):
    fixture = str(FIXTURES_DIR / "sample_transcript.jsonl")
    payload = json.dumps({"transcript_path": fixture, "session_id": "test-no-compact"})

    import io
    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ch.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    assert captured.getvalue().strip() == ""


def test_main_creates_context_and_returns_additional_context(tmp_path):
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    payload = json.dumps({
        "transcript_path": fixture,
        "session_id": "compact-integ-test"
    })

    import io
    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout=f"{tmp_path}\n"),  # find_project_root: git show-toplevel
            mock.Mock(returncode=0, stdout=MOCK_NARRATION),   # call_claude_narration: claude -p
            mock.Mock(returncode=128, stdout=""),              # get_git_commits: git is-inside-work-tree
            mock.Mock(returncode=128, stdout=""),              # get_git_head: git rev-parse HEAD
        ]
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ch.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    session_dir = tmp_path / ".claude" / "sessions" / "compact-integ-test"
    assert (session_dir / "INDEX.md").exists()

    contexts = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(contexts) == 1
    assert "api-setup" in contexts[0].name

    index_content = (session_dir / "INDEX.md").read_text()
    assert "compact-uuid-001" in index_content

    output = captured.getvalue().strip()
    assert output, "main() did not output additionalContext"
    data = json.loads(output)
    assert "additionalContext" in data.get("hookSpecificOutput", {})
    assert "현재 세션 컨텍스트" in data["hookSpecificOutput"]["additionalContext"]


def test_main_deduplicates_same_compact(tmp_path):
    fixture = str(FIXTURES_DIR / "compact_transcript.jsonl")
    payload = json.dumps({
        "transcript_path": fixture,
        "session_id": "compact-dedup-test"
    })

    # First call: creates CONTEXT
    import io
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout=f"{tmp_path}\n"),
            mock.Mock(returncode=0, stdout=MOCK_NARRATION),
            mock.Mock(returncode=128, stdout=""),
            mock.Mock(returncode=128, stdout=""),
        ]
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", io.StringIO()):
                ch.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    # Second call: same compact → no new CONTEXT, no output
    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ch.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    session_dir = tmp_path / ".claude" / "sessions" / "compact-dedup-test"
    contexts = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(contexts) == 1
    assert captured.getvalue().strip() == ""
