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
