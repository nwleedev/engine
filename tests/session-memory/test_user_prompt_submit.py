# tests/session-memory/test_user_prompt_submit.py
import io, json, sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import user_prompt_submit as ups


def test_no_flag_exits_without_output(tmp_path):
    """No flag file → exit without any stdout output."""
    session_id = "sess-no-flag"
    payload = json.dumps({"session_id": session_id, "cwd": str(tmp_path)})

    captured = io.StringIO()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ups.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    assert captured.getvalue().strip() == ""


def test_flag_returns_additional_context_and_deletes_flag(tmp_path):
    """Flag present + context files → return additionalContext, delete flag."""
    session_id = "sess-with-flag"
    sessions_dir = tmp_path / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True)

    flag_path = sessions_dir / f"compacted.{session_id}.flag"
    flag_path.write_text(session_id, encoding="utf-8")

    session_dir = sessions_dir / session_id
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    (contexts_dir / "CONTEXT-20260424-1200-test.md").write_text("이전 작업 내용", encoding="utf-8")

    payload = json.dumps({"session_id": session_id, "cwd": str(tmp_path)})
    captured = io.StringIO()

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ups.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    assert not flag_path.exists(), "Flag must be deleted after injection"
    output = captured.getvalue().strip()
    assert output, "additionalContext JSON must be printed"
    data = json.loads(output)
    assert data["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "이전 작업 내용" in data["hookSpecificOutput"]["additionalContext"]


def test_flag_deleted_even_when_no_context_files(tmp_path):
    """Flag must be deleted even when no context files exist."""
    session_id = "sess-no-context"
    sessions_dir = tmp_path / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True)

    flag_path = sessions_dir / f"compacted.{session_id}.flag"
    flag_path.write_text(session_id, encoding="utf-8")

    payload = json.dumps({"session_id": session_id, "cwd": str(tmp_path)})
    captured = io.StringIO()

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ups.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    assert not flag_path.exists(), "Flag must be deleted even with no context files"
    assert captured.getvalue().strip() == ""


def test_parallel_session_isolation(tmp_path):
    """Different session IDs have isolated flag files."""
    sessions_dir = tmp_path / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True)

    session_a = "sess-parallel-A"
    session_b = "sess-parallel-B"
    flag_a = sessions_dir / f"compacted.{session_a}.flag"
    flag_a.write_text(session_a, encoding="utf-8")

    payload = json.dumps({"session_id": session_b, "cwd": str(tmp_path)})
    captured = io.StringIO()

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            with mock.patch("sys.stdout", captured):
                ups.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    assert flag_a.exists(), "Session A flag must not be touched by session B"
    assert captured.getvalue().strip() == ""


def test_malformed_payload_exits_silently():
    """Invalid JSON payload must exit without raising."""
    captured = io.StringIO()
    sys.stdin = io.StringIO("not-valid-json")
    try:
        with mock.patch("sys.stdout", captured):
            ups.main()
    except SystemExit:
        pass
    finally:
        sys.stdin = sys.__stdin__

    assert captured.getvalue().strip() == ""


def test_flag_prints_context_filenames_to_stderr(tmp_path, capsys):
    """Flag present + context files → stderr shows injected filenames."""
    session_id = "sess-stderr-log"
    sessions_dir = tmp_path / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True)

    flag_path = sessions_dir / f"compacted.{session_id}.flag"
    flag_path.write_text(session_id, encoding="utf-8")

    session_dir = sessions_dir / session_id
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    (contexts_dir / "CONTEXT-20260427-1200-foo.md").write_text("content", encoding="utf-8")

    payload = json.dumps({"session_id": session_id, "cwd": str(tmp_path)})

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        sys.stdin = io.StringIO(payload)
        try:
            ups.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = sys.__stdin__

    captured = capsys.readouterr()
    assert "[session-memory] post-compact inject:" in captured.err
    assert "CONTEXT-20260427-1200-foo.md" in captured.err
