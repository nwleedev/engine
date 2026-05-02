import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_resume_prompt():
    spec = importlib.util.spec_from_file_location("resume_prompt", SCRIPTS / "resume_prompt.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_builds_short_actionable_prompt(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\nlast_processed_offset: 10\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        "- [CONTEXT-1.md] — 자동 저장 정책을 분리했다.\n"
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Policy Update\n\n## 다음\nSessionStart 주입을 구현한다.\n\n"
        "## Evidence\n\n### Files\n- plugins/codex-session-memory/scripts/policy.py\n"
    )
    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=1200)
    assert "current_goal" in prompt
    assert "next_action" in prompt
    assert "SessionStart 주입을 구현한다" in prompt
    assert "plugins/codex-session-memory/scripts/policy.py" in prompt
