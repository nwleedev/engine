import os, sys, json, tempfile
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import handwrite_context as hw

def test_parse_transcript_extracts_cwd():
    cwd, messages = hw.parse_transcript(str(FIXTURES_DIR / "sample_transcript.jsonl"))
    assert cwd == "/Users/test/myproject"

def test_parse_transcript_extracts_messages():
    cwd, messages = hw.parse_transcript(str(FIXTURES_DIR / "sample_transcript.jsonl"))
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert messages[0]["text"] == "JWT 인증을 구현해줘"
    assert messages[0]["uuid"] == "msg-001"

def test_parse_transcript_handles_list_content():
    cwd, messages = hw.parse_transcript(str(FIXTURES_DIR / "sample_transcript.jsonl"))
    assert messages[1]["text"] == "JWT 토큰 발급 로직을 구현하겠습니다."

def test_extract_text_string():
    assert hw.extract_text("hello") == "hello"

def test_extract_text_list():
    content = [{"type": "text", "text": "hello"}, {"type": "tool_use", "id": "t1"}]
    assert hw.extract_text(content) == "hello"

def test_extract_delta_from_none():
    messages = [{"uuid": "a"}, {"uuid": "b"}, {"uuid": "c"}]
    assert hw.extract_delta(messages, None) == messages

def test_extract_delta_from_uuid():
    messages = [{"uuid": "a"}, {"uuid": "b"}, {"uuid": "c"}]
    result = hw.extract_delta(messages, "b")
    assert result == [{"uuid": "c"}]

def test_extract_delta_uuid_not_found():
    messages = [{"uuid": "a"}, {"uuid": "b"}]
    # UUID not found means transcript rotated; fallback returns all messages
    result = hw.extract_delta(messages, "z")
    assert result == messages

def test_format_messages():
    messages = [
        {"role": "user", "text": "질문"},
        {"role": "assistant", "text": "답변"},
    ]
    result = hw.format_messages(messages)
    assert result == "[user] 질문\n[assistant] 답변"

def test_truncate_messages_under_limit():
    messages = [{"role": "user", "text": "짧은 메시지", "uuid": "a"}]
    text, was_truncated = hw.truncate_messages(messages)
    assert was_truncated is False
    assert "[user] 짧은 메시지" in text

def test_truncate_messages_over_limit():
    long_msg = "가" * 80_001
    messages = [
        {"role": "user", "text": "앞부분 메시지", "uuid": "a"},
        {"role": "assistant", "text": long_msg, "uuid": "b"},
        {"role": "user", "text": "최근 메시지", "uuid": "c"},
    ]
    text, was_truncated = hw.truncate_messages(messages)
    assert was_truncated is True
    assert "최근 메시지" in text
    assert len(text) <= hw.CHAR_LIMIT + 100

def test_parse_frontmatter_basic():
    content = "---\nsession_id: abc123\ncwd: /tmp/proj\n---\n\n# 요약\n본문"
    fm, body = hw.parse_frontmatter(content)
    assert fm["session_id"] == "abc123"
    assert fm["cwd"] == "/tmp/proj"
    assert "# 요약" in body

def test_parse_frontmatter_no_frontmatter():
    content = "# 그냥 마크다운"
    fm, body = hw.parse_frontmatter(content)
    assert fm == {}
    assert body == content

def test_read_index_returns_none_when_missing(tmp_path):
    result = hw.read_index(tmp_path / "nonexistent")
    assert result is None

def test_read_index_returns_frontmatter(tmp_path):
    session_dir = tmp_path / "sess1"
    session_dir.mkdir()
    (session_dir / "INDEX.md").write_text(
        "---\nsession_id: sess1\nlast_processed_uuid: uuid-x\ncontext_head: abc\n---\n\n# 요약\n"
    )
    data = hw.read_index(session_dir)
    assert data["session_id"] == "sess1"
    assert data["last_processed_uuid"] == "uuid-x"

def test_create_index_writes_file(tmp_path):
    session_dir = tmp_path / "sess2"
    data = hw.create_index(session_dir, "sess2", "/tmp/proj")
    assert (session_dir / "INDEX.md").exists()
    assert data["session_id"] == "sess2"
    assert data.get("last_processed_uuid", "") == ""
    assert data.get("last_context_written_at", "MISSING") == ""

def test_update_index_appends_context_entry(tmp_path):
    session_dir = tmp_path / "sess3"
    hw.create_index(session_dir, "sess3", "/tmp/proj")
    hw.update_index(
        session_dir,
        hw.read_index(session_dir),
        last_uuid="uuid-new",
        new_head="def456",
        context_num=1,
        title="test-work",
        one_liner="테스트 작업을 완료했다",
    )
    content = (session_dir / "INDEX.md").read_text()
    assert "uuid-new" in content
    assert "[0001] test-work" in content

def test_get_next_context_number_empty_dir(tmp_path):
    contexts_dir = tmp_path / "contexts"
    contexts_dir.mkdir()
    assert hw.get_next_context_number(tmp_path) == 1

def test_get_next_context_number_with_existing(tmp_path):
    contexts_dir = tmp_path / "contexts"
    contexts_dir.mkdir()
    (contexts_dir / "CONTEXT-0001-foo.md").write_text("")
    (contexts_dir / "CONTEXT-0002-bar.md").write_text("")
    assert hw.get_next_context_number(tmp_path) == 3

def test_write_context_file_creates_file(tmp_path):
    (tmp_path / "contexts").mkdir()
    hw.write_context_file(
        session_dir=tmp_path,
        num=1,
        title="jwt-setup",
        narration="JWT를 구현했습니다.",
        commits=["abc1234 feat: add jwt"],
        session_id="sess-abc",
    )
    files = list((tmp_path / "contexts").glob("CONTEXT-0001-*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "JWT를 구현했습니다." in content
    assert "abc1234" in content
    assert "claude -r sess-abc" in content

def test_write_context_file_no_commits(tmp_path):
    (tmp_path / "contexts").mkdir()
    hw.write_context_file(tmp_path, 1, "quick-fix", "간단히 수정했습니다.", [], "sess-xyz")
    files = list((tmp_path / "contexts").glob("CONTEXT-0001-*.md"))
    content = files[0].read_text()
    assert "관련 커밋" not in content

def test_find_project_root_uses_git_root(tmp_path):
    sub = tmp_path / "web"
    sub.mkdir()
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout=f"{tmp_path}\n")
        result = hw.find_project_root(str(sub))
    assert result == str(tmp_path)

def test_find_project_root_walks_up_to_claude_dir(tmp_path):
    (tmp_path / ".claude").mkdir()
    sub = tmp_path / "web" / "src"
    sub.mkdir(parents=True)
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=128, stdout="")
        result = hw.find_project_root(str(sub))
    assert result == str(tmp_path)

def test_find_project_root_returns_cwd_when_no_git_no_claude(tmp_path):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=128, stdout="")
        result = hw.find_project_root(str(tmp_path))
    assert result == str(tmp_path)

def test_get_git_head_returns_hash(tmp_path):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout="abc1234\n")
        result = hw.get_git_head(str(tmp_path))
    assert result == "abc1234"

def test_get_git_head_returns_empty_on_error(tmp_path):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=128, stdout="")
        result = hw.get_git_head(str(tmp_path))
    assert result == ""

def test_get_git_commits_with_context_head(tmp_path):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout="true\n"),
            mock.Mock(returncode=0, stdout="abc1234 feat: add jwt\ndef5678 fix: typo\n"),
        ]
        commits = hw.get_git_commits(str(tmp_path), "prev-head", None)
    assert commits == ["abc1234 feat: add jwt", "def5678 fix: typo"]

def test_get_git_commits_no_git(tmp_path):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=128, stdout="")
        commits = hw.get_git_commits(str(tmp_path), None, None)
    assert commits == []

MOCK_CLAUDE_RESPONSE = json.dumps({
    "type": "result",
    "subtype": "success",
    "result": json.dumps({
        "title": "jwt-token-setup",
        "narration": "JWT 토큰 발급을 구현했습니다. 만료 시간은 15분입니다."
    })
})

def test_call_claude_narration_success():
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=MOCK_CLAUDE_RESPONSE
        )
        result = hw.call_claude_narration("대화 내역", was_truncated=False)
    assert result["title"] == "jwt-token-setup"
    assert "JWT" in result["narration"]

def test_call_claude_narration_invalid_json():
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout='{"result": "not json"}')
        result = hw.call_claude_narration("대화 내역", was_truncated=False)
    assert result is None

def test_call_claude_narration_strips_code_fences():
    inner = '{"title": "jwt-setup", "narration": "JWT를 구현했습니다."}'
    fenced = f"```json\n{inner}\n```"
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps({"type": "result", "result": fenced})
        )
        result = hw.call_claude_narration("대화 내역", was_truncated=False)
    assert result["title"] == "jwt-setup"
    assert "JWT" in result["narration"]

def test_call_claude_narration_subprocess_error():
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=1, stdout="")
        result = hw.call_claude_narration("대화 내역", was_truncated=False)
    assert result is None

def test_build_prompt_includes_truncation_note():
    prompt = hw.build_prompt("메시지", was_truncated=True)
    assert "앞부분 생략" in prompt

def test_call_claude_sets_env_var():
    captured_env = {}
    def fake_run(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        return mock.Mock(returncode=0, stdout=MOCK_CLAUDE_RESPONSE)
    with mock.patch("subprocess.run", side_effect=fake_run):
        hw.call_claude_narration("메시지", was_truncated=False)
    assert captured_env.get("CLAUDE_WRITING_CONTEXT") == "1"

MOCK_NARRATION = json.dumps({
    "type": "result", "subtype": "success",
    "result": json.dumps({
        "title": "jwt-setup",
        "narration": "JWT 인증을 구현하고 만료 시간을 15분으로 설정했습니다. 갱신 로직은 미완료입니다."
    })
})

def test_main_creates_context_file(tmp_path):
    fixture = str(FIXTURES_DIR / "sample_transcript.jsonl")
    payload = json.dumps({"transcript_path": fixture, "session_id": "test-sess-001"})

    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            mock.Mock(returncode=0, stdout=f"{tmp_path}\n"),  # git show-toplevel (find_project_root)
            mock.Mock(returncode=0, stdout=MOCK_NARRATION),   # claude -p narration
            mock.Mock(returncode=128, stdout=""),              # git rev-parse (get_git_commits check)
            mock.Mock(returncode=128, stdout=""),              # git rev-parse HEAD (get_git_head)
        ]
        original_parse = hw.parse_transcript
        def patched_parse(path):
            cwd, msgs = original_parse(path)
            return str(tmp_path), msgs
        with mock.patch.object(hw, "parse_transcript", side_effect=patched_parse):
            import io
            sys.stdin = io.StringIO(payload)
            try:
                hw.main()
            except SystemExit:
                pass
            finally:
                sys.stdin = sys.__stdin__

    session_dir = tmp_path / ".claude" / "sessions" / "test-sess-001"
    assert (session_dir / "INDEX.md").exists()
    contexts = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(contexts) == 1
    assert "jwt-setup" in contexts[0].name

def test_narration_parses_json_with_insight_prefix():
    """Mode 1: ★ Insight block appears BEFORE the JSON."""
    inner = (
        "`★ Insight ─────────────────────────────────────`\n"
        "some insight text\n"
        "`─────────────────────────────────────────────────`\n\n"
        '{"title": "my-work", "narration": "작업 완료"}'
    )
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps({"type": "result", "subtype": "success", "result": inner}),
        )
        result = hw.call_claude_narration("대화", was_truncated=False)
    assert result == {"title": "my-work", "narration": "작업 완료"}


def test_narration_parses_json_with_insight_suffix():
    """Mode 2: ★ Insight block appears AFTER the JSON (trailing content)."""
    inner = (
        '{"title": "my-work", "narration": "작업 완료"}\n\n'
        "`★ Insight ─────────────────────────────────────`\n"
        "some insight text\n"
        "`─────────────────────────────────────────────────`"
    )
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps({"type": "result", "subtype": "success", "result": inner}),
        )
        result = hw.call_claude_narration("대화", was_truncated=False)
    assert result == {"title": "my-work", "narration": "작업 완료"}


def test_narration_returns_none_when_no_json():
    """Mode 3: No JSON in response — return None, not a garbage dict."""
    inner = "파일 쓰기 권한을 허용해 주세요."
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps({"type": "result", "subtype": "success", "result": inner}),
        )
        result = hw.call_claude_narration("대화", was_truncated=False)
    assert result is None


def test_narration_skips_curly_braces_in_code():
    """{ inside a Python code block are skipped; the real JSON found after."""
    inner = (
        "```python\n"
        "re.compile(r'{pattern}')\n"
        "```\n\n"
        '{"title": "code-task", "narration": "코드 작업"}'
    )
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            returncode=0,
            stdout=json.dumps({"type": "result", "subtype": "success", "result": inner}),
        )
        result = hw.call_claude_narration("대화", was_truncated=False)
    assert result == {"title": "code-task", "narration": "코드 작업"}


def test_main_exits_when_recursive_guard_set():
    with mock.patch.dict(os.environ, {"CLAUDE_WRITING_CONTEXT": "1"}):
        with mock.patch("sys.exit", side_effect=SystemExit(0)) as mock_exit:
            try:
                hw.main()
            except SystemExit:
                pass
            mock_exit.assert_called_with(0)



_SAMPLE_INSIGHT_MSG = (
    "`★ Insight ─────────────────────────────────────────────`\n"
    "핵심 인사이트 내용입니다.\n"
    "`─────────────────────────────────────────────────`"
)


def test_extract_insights_finds_blocks():
    messages = [{"role": "assistant", "text": _SAMPLE_INSIGHT_MSG}]
    result = hw.extract_insights(messages)
    assert result == ["핵심 인사이트 내용입니다."]


def test_extract_insights_skips_user_messages():
    messages = [{"role": "user", "text": _SAMPLE_INSIGHT_MSG}]
    result = hw.extract_insights(messages)
    assert result == []


def test_extract_insights_empty_when_no_blocks():
    messages = [{"role": "assistant", "text": "일반 텍스트입니다."}]
    result = hw.extract_insights(messages)
    assert result == []
