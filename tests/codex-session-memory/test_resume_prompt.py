import importlib.util
import os
import sys
import types
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"
RESUME = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "skills" / "resume" / "resume.py"


def load_resume_prompt():
    spec = importlib.util.spec_from_file_location("resume_prompt", SCRIPTS / "resume_prompt.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_resume_skill():
    spec = importlib.util.spec_from_file_location("codex_session_memory_resume_skill_test", RESUME)
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


def test_uses_index_context_order_when_mtime_conflicts(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        "- [CONTEXT-new.md] — durable latest\n"
        "- [CONTEXT-old.md] — stale but newer mtime\n"
    )
    new_context = contexts / "CONTEXT-new.md"
    old_context = contexts / "CONTEXT-old.md"
    new_context.write_text("# New\n\n## 다음\nINDEX 순서의 최신 작업을 계속한다.\n")
    old_context.write_text("# Old\n\n## 다음\nmtime 기준이면 이 오래된 작업이 먼저 나온다.\n")
    os.utime(new_context, (100, 100))
    os.utime(old_context, (200, 200))

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=1600)

    assert prompt.index("--- CONTEXT-new.md ---") < prompt.index("--- CONTEXT-old.md ---")
    assert "INDEX 순서의 최신 작업을 계속한다" in prompt


def test_uses_latest_three_contexts_from_writer_append_order(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        "- [CONTEXT-1.md] — first appended\n"
        "- [CONTEXT-2.md] — second appended\n"
        "- [CONTEXT-3.md] — third appended\n"
        "- [CONTEXT-4.md] — fourth appended\n"
    )
    for index in range(1, 5):
        (contexts / f"CONTEXT-{index}.md").write_text(
            f"# Context {index}\n\n## 다음\nCONTEXT-{index} next action\n"
        )

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=2200)

    assert "--- CONTEXT-1.md ---" not in prompt
    assert "CONTEXT-1 next action" not in prompt
    assert "--- CONTEXT-2.md ---" in prompt
    assert "--- CONTEXT-3.md ---" in prompt
    assert "--- CONTEXT-4.md ---" in prompt
    assert "CONTEXT-4 next action" in prompt


def test_preserves_root_config_and_plugin_file_evidence(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — evidence\n"
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Evidence\n\n## Evidence\n\n### Files\n"
        "- README.md\n"
        "- pyproject.toml\n"
        "- .codex-plugin/plugin.json\n"
        "- plugins/codex-session-memory/scripts/resume_prompt.py\n"
        "- 없음\n"
    )

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=1600)

    assert "- README.md" in prompt
    assert "- pyproject.toml" in prompt
    assert "- .codex-plugin/plugin.json" in prompt
    assert "- plugins/codex-session-memory/scripts/resume_prompt.py" in prompt
    assert "- 없음" not in prompt


def test_preserves_structure_and_next_action_with_tight_budget(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — many files\n"
    )
    long_files = "\n".join(
        f"- plugins/codex-session-memory/scripts/{index:02d}-very-long-path-name-for-budget-testing.py"
        for index in range(60)
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Many Files\n\n## 다음\n작은 예산에서도 다음 행동을 유지한다.\n\n"
        f"## Evidence\n\n### Files\n{long_files}\n"
    )

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=700)

    assert len(prompt) <= 700
    assert "next_action:" in prompt
    assert "작은 예산에서도 다음 행동을 유지한다" in prompt
    assert prompt.endswith("</codex-session-memory>")


def test_preserves_closing_tag_with_very_small_budgets(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — small budget\n"
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Small Budget\n\n## 다음\n작은 예산에서도 태그를 보존한다.\n"
    )

    for budget in (80, 100, 120):
        prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=budget)

        assert len(prompt) <= budget
        assert prompt.startswith("<codex-session-memory>")
        assert prompt.endswith("</codex-session-memory>")


def test_resume_skill_ignores_preloaded_sibling_modules(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    session = project / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\nlast_updated: 2026-05-02T00:00:00Z\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — resume\n"
    )
    (contexts / "CONTEXT-1.md").write_text("# Resume\n\n## 다음\n파일 경로 로더를 사용한다.\n")
    fake_dotenv = types.ModuleType("dotenv_loader")
    fake_dotenv.load_project_dotenv = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("wrong dotenv"))
    fake_project_root = types.ModuleType("project_root")
    fake_project_root.find_project_root = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("wrong root"))
    fake_index_io = types.ModuleType("index_io")
    fake_index_io.read_frontmatter = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("wrong index"))
    fake_resume_prompt = types.ModuleType("resume_prompt")
    fake_resume_prompt.build_resume_prompt = lambda *_args, **_kwargs: "wrong prompt"
    monkeypatch.setitem(sys.modules, "dotenv_loader", fake_dotenv)
    monkeypatch.setitem(sys.modules, "project_root", fake_project_root)
    monkeypatch.setitem(sys.modules, "index_io", fake_index_io)
    monkeypatch.setitem(sys.modules, "resume_prompt", fake_resume_prompt)
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "abc123"]) == 0
    output = capsys.readouterr().out
    assert "파일 경로 로더를 사용한다" in output
    assert "wrong prompt" not in output


def test_resume_skill_output_stays_within_prompt_budget(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    session = project / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\nlast_updated: 2026-05-02T00:00:00Z\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — budget\n"
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Budget\n\n## 다음\n출력은 닫는 태그로 끝난다.\n\n" + ("detail\n" * 2000)
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "abc123"]) == 0
    output = capsys.readouterr().out
    assert len(output) <= resume_skill.MAX_INJECT_CHARS
    assert output.endswith("</codex-session-memory>")
