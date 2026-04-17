import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import compact_handler as ch
import handwrite_context as hw


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


