import importlib.util
import os
import sqlite3
import sys
import types
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"
RESUME = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "skills" / "resume" / "resume.py"


def load_resume_prompt():
    spec = importlib.util.spec_from_file_location("resume_prompt", SCRIPTS / "resume_prompt.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_resume_skill():
    spec = importlib.util.spec_from_file_location("codex_session_memory_resume_skill_test", RESUME)
    assert spec is not None
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
        "# Policy Update\n\n## 다음\nresume handoff를 구현한다.\n\n"
        "## Evidence\n\n### Files\n- plugins/codex/session-memory/scripts/session_locator.py\n"
    )
    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=1200)
    assert "current_goal" in prompt
    assert "next_action" in prompt
    assert "resume handoff를 구현한다" in prompt
    assert "plugins/codex/session-memory/scripts/session_locator.py" in prompt


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


def test_dedupes_duplicate_index_filenames_using_latest_append_event(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        "- [CONTEXT-1.md] — first event\n"
        "- [CONTEXT-2.md] — second event\n"
        "- [CONTEXT-1.md] — latest event for same HH00 file\n"
        "- [CONTEXT-3.md] — third file\n"
    )
    for index in range(1, 4):
        (contexts / f"CONTEXT-{index}.md").write_text(
            f"# Context {index}\n\n## 다음\nCONTEXT-{index} next action\n"
        )

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=2600)

    assert prompt.count("--- CONTEXT-1.md ---") == 1
    assert prompt.index("--- CONTEXT-2.md ---") < prompt.index("--- CONTEXT-1.md ---")
    assert prompt.index("--- CONTEXT-1.md ---") < prompt.index("--- CONTEXT-3.md ---")


def test_uses_latest_three_contexts_with_collision_safe_writer_names(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    context_names = [
        "CONTEXT-20260502-1200-A.md",
        "CONTEXT-20260502-1200-A-2.md",
        "CONTEXT-20260502-1201-B.md",
        "CONTEXT-20260502-1202-C.md",
    ]
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc123\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        + "".join(f"- [{name}] — writer append order\n" for name in context_names)
    )
    for name in context_names:
        (contexts / name).write_text(f"# {name}\n\n## 다음\nnext action for {name}\n")

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=2600)

    assert "--- CONTEXT-20260502-1200-A.md ---" not in prompt
    assert "next action for CONTEXT-20260502-1200-A.md" not in prompt
    assert "--- CONTEXT-20260502-1200-A-2.md ---" in prompt
    assert "--- CONTEXT-20260502-1201-B.md ---" in prompt
    assert "--- CONTEXT-20260502-1202-C.md ---" in prompt
    assert "next action for CONTEXT-20260502-1202-C.md" in prompt


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
        "- plugins/codex/session-memory/scripts/resume_prompt.py\n"
        "- 없음\n"
    )

    prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=1600)

    assert "- README.md" in prompt
    assert "- pyproject.toml" in prompt
    assert "- .codex-plugin/plugin.json" in prompt
    assert "- plugins/codex/session-memory/scripts/resume_prompt.py" in prompt
    assert "- 없음" not in prompt


def test_preserves_structure_and_next_action_with_tight_budget(tmp_path):
    session = tmp_path / ".codex" / "sessions" / "abc123"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — many files\n"
    )
    long_files = "\n".join(
        f"- plugins/codex/session-memory/scripts/{index:02d}-very-long-path-name-for-budget-testing.py"
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

    for budget in range(80, 201):
        prompt = load_resume_prompt().build_resume_prompt(session, budget_chars=budget)

        assert len(prompt) <= budget
        assert prompt.startswith("<codex-session-memory>")
        assert prompt.endswith("</codex-session-memory>")


def test_build_resume_prompt_includes_child_summary_when_provided(tmp_path):
    parent = tmp_path / ".codex" / "session-memory" / "threads" / "parent123-session"
    parent_contexts = parent / "contexts"
    parent_contexts.mkdir(parents=True)
    (parent / "INDEX.md").write_text(
        "---\nthread_id: parent123-session\n---\n\n"
        "# Parent\n\n## 컨텍스트 목록\n\n- [CONTEXT-parent.md] — parent\n",
        encoding="utf-8",
    )
    (parent_contexts / "CONTEXT-parent.md").write_text(
        "# Parent\n\n## 다음\nparent 작업을 계속한다.\n",
        encoding="utf-8",
    )
    child = tmp_path / ".codex" / "session-memory" / "threads" / "child123-session"
    child_contexts = child / "contexts"
    child_contexts.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nthread_id: child123-session\n---\n\n"
        "# Child\n\n## 컨텍스트 목록\n\n- [CONTEXT-child.md] — child\n",
        encoding="utf-8",
    )
    (child_contexts / "CONTEXT-child.md").write_text(
        "# Child\n\n## 다음\nchild summary를 parent resume에 제공한다.\n\n"
        "## Evidence\n\n### Files\n- 없음\n",
        encoding="utf-8",
    )

    prompt = load_resume_prompt().build_resume_prompt(
        parent,
        budget_chars=2200,
        related_session_dirs=[child],
    )

    assert "--- CONTEXT-parent.md ---" in prompt
    assert "parent 작업을 계속한다" in prompt
    assert "--- related:child123-session:CONTEXT-child.md ---" in prompt
    assert "child summary를 parent resume에 제공한다" in prompt
    assert "- 없음" not in prompt


def test_build_resume_prompt_preserves_parent_and_child_with_tight_budget(tmp_path):
    parent = tmp_path / ".codex" / "session-memory" / "threads" / "parent123-session"
    parent_contexts = parent / "contexts"
    parent_contexts.mkdir(parents=True)
    (parent / "INDEX.md").write_text(
        "---\nthread_id: parent123-session\n---\n\n"
        "# Parent\n\n## 컨텍스트 목록\n\n- [CONTEXT-parent.md] — parent\n",
        encoding="utf-8",
    )
    (parent_contexts / "CONTEXT-parent.md").write_text(
        "# Parent\n\n## 다음\nparent critical next action remains.\n\n"
        + ("parent detail fills the tight next_action budget.\n" * 60),
        encoding="utf-8",
    )
    child = tmp_path / ".codex" / "session-memory" / "threads" / "child123-session"
    child_contexts = child / "contexts"
    child_contexts.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nthread_id: child123-session\n---\n\n"
        "# Child\n\n## 컨텍스트 목록\n\n- [CONTEXT-child.md] — child\n",
        encoding="utf-8",
    )
    (child_contexts / "CONTEXT-child.md").write_text(
        "# Child\n\n## 다음\nchild critical summary remains.\n",
        encoding="utf-8",
    )

    prompt = load_resume_prompt().build_resume_prompt(
        parent,
        budget_chars=900,
        related_session_dirs=[child],
    )

    assert len(prompt) <= 900
    assert "parent critical next action remains." in prompt
    assert "child critical summary remains." in prompt
    assert prompt.endswith("</codex-session-memory>")


def test_resume_skill_ignores_preloaded_sibling_modules(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    session = project / ".codex" / "sessions" / "abc12345"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc12345\nlast_updated: 2026-05-02T00:00:00Z\n---\n\n"
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

    assert resume_skill.main(["resume.py", "abc12345"]) == 0
    output = capsys.readouterr().out
    assert "파일 경로 로더를 사용한다" in output
    assert "wrong prompt" not in output


def test_resume_skill_output_stays_within_prompt_budget(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    session = project / ".codex" / "sessions" / "abc12345"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nsession_id: abc12345\nlast_updated: 2026-05-02T00:00:00Z\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — budget\n"
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Budget\n\n## 다음\n출력은 닫는 태그로 끝난다.\n\n" + ("detail\n" * 2000)
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "abc12345"]) == 0
    output = capsys.readouterr().out
    assert len(output) <= resume_skill.MAX_INJECT_CHARS
    assert output.endswith("</codex-session-memory>")


def test_resume_skill_lists_flat_artifact_and_legacy_sessions(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    flat_session = project / ".codex" / "session-memory" / "threads" / "flat1234-session"
    flat_session.mkdir(parents=True)
    (flat_session / "INDEX.md").write_text(
        "---\nthread_id: flat1234-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    legacy_session = project / ".codex" / "sessions" / "legacy99-session"
    legacy_session.mkdir(parents=True)
    (legacy_session / "INDEX.md").write_text(
        "---\nsession_id: legacy99-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py"]) == 0
    output = capsys.readouterr().out
    assert "flat1234" in output
    assert "legacy99" in output


def test_resume_skill_lists_legacy_children_artifacts(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    legacy_child = project / ".codex" / "sessions" / "_children" / "child1234-session"
    legacy_child.mkdir(parents=True)
    (legacy_child / "INDEX.md").write_text(
        "---\nsession_id: child1234-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy Child\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py"]) == 0
    output = capsys.readouterr().out
    assert "child123" in output
    assert "_children" not in output


def test_resume_skill_prefers_flat_artifact_over_duplicate_legacy_session(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    flat_session = project / ".codex" / "session-memory" / "threads" / "same1234-session"
    flat_session.mkdir(parents=True)
    (flat_session / "INDEX.md").write_text(
        "---\nthread_id: same1234-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    legacy_session = project / ".codex" / "sessions" / "same1234-session"
    legacy_session.mkdir(parents=True)
    (legacy_session / "INDEX.md").write_text(
        "---\nsession_id: same1234-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    rows = resume_skill.list_sessions(str(project), limit=None)

    assert len(rows) == 1
    assert rows[0]["path"] == flat_session / "INDEX.md"


def test_resume_skill_prefers_flat_artifact_over_duplicate_legacy_child_session(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    flat_session = project / ".codex" / "session-memory" / "threads" / "same1234-session"
    flat_session.mkdir(parents=True)
    (flat_session / "INDEX.md").write_text(
        "---\nthread_id: same1234-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    legacy_child = project / ".codex" / "sessions" / "_children" / "same1234-session"
    legacy_child.mkdir(parents=True)
    (legacy_child / "INDEX.md").write_text(
        "---\nsession_id: same1234-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy Child\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    rows = resume_skill.list_sessions(str(project), limit=None)

    assert len(rows) == 1
    assert rows[0]["path"] == flat_session / "INDEX.md"


def test_resume_skill_resumes_legacy_child_artifact_by_prefix(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    legacy_child = project / ".codex" / "sessions" / "_children" / "child1234-session"
    contexts = legacy_child / "contexts"
    contexts.mkdir(parents=True)
    (legacy_child / "INDEX.md").write_text(
        "---\nsession_id: child1234-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy Child\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — resume\n",
        encoding="utf-8",
    )
    (contexts / "CONTEXT-1.md").write_text(
        "# Legacy Child\n\n## 다음\nlegacy child artifact를 prefix로 resume한다.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "child123"]) == 0
    assert "legacy child artifact를 prefix로 resume한다" in capsys.readouterr().out


def test_resume_skill_includes_graph_child_flat_artifact_context(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    parent = project / ".codex" / "session-memory" / "threads" / "parent12-session"
    parent_contexts = parent / "contexts"
    parent_contexts.mkdir(parents=True)
    (parent / "INDEX.md").write_text(
        "---\nthread_id: parent12-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Parent\n\n## 컨텍스트 목록\n\n- [CONTEXT-parent.md] — parent\n",
        encoding="utf-8",
    )
    (parent_contexts / "CONTEXT-parent.md").write_text(
        "# Parent\n\n## 다음\nparent CLI resume를 계속한다.\n",
        encoding="utf-8",
    )
    child = project / ".codex" / "session-memory" / "threads" / "child123-session"
    child_contexts = child / "contexts"
    child_contexts.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nthread_id: child123-session\nlast_updated: 2026-05-04T00:05:00Z\n---\n\n"
        "# Child\n\n## 컨텍스트 목록\n\n- [CONTEXT-child.md] — child\n",
        encoding="utf-8",
    )
    (child_contexts / "CONTEXT-child.md").write_text(
        "# Child\n\n## 다음\ngraph child context를 CLI resume에 포함한다.\n",
        encoding="utf-8",
    )
    grandchild = project / ".codex" / "session-memory" / "threads" / "grand123-session"
    grandchild_contexts = grandchild / "contexts"
    grandchild_contexts.mkdir(parents=True)
    (grandchild / "INDEX.md").write_text(
        "---\nthread_id: grand123-session\nlast_updated: 2026-05-04T00:06:00Z\n---\n\n"
        "# Grandchild\n\n## 컨텍스트 목록\n\n- [CONTEXT-grandchild.md] — grandchild\n",
        encoding="utf-8",
    )
    (grandchild_contexts / "CONTEXT-grandchild.md").write_text(
        "# Grandchild\n\n## 다음\ngrandchild context는 direct child가 아니다.\n",
        encoding="utf-8",
    )
    legacy_child = project / ".codex" / "sessions" / "legacy99-child"
    legacy_child.mkdir(parents=True)
    (legacy_child / "INDEX.md").write_text(
        "---\nsession_id: legacy99-child\nlast_updated: 2026-05-04T00:10:00Z\n---\n\n"
        "# Legacy Child\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()
    real_loader = resume_skill.load_script_module

    class FakeGraphStore:
        def __init__(self, *args, **kwargs):
            pass

        def children_of(self, thread_id):
            assert thread_id == "parent12-session"
            return ["child123-session", "legacy99-child", "missing99-child"]

        def descendants_of(self, thread_id):
            raise AssertionError("resume must only read direct children")

    fake_graph_store = types.SimpleNamespace(GraphStore=FakeGraphStore)

    def fake_loader(filename, module_name):
        if filename == "graph_store.py":
            return fake_graph_store
        return real_loader(filename, module_name)

    monkeypatch.setattr(resume_skill, "load_script_module", fake_loader)

    assert resume_skill.main(["resume.py", "parent12"]) == 0
    output = capsys.readouterr().out
    assert "parent CLI resume를 계속한다" in output
    assert "graph child context를 CLI resume에 포함한다" in output
    assert "grandchild context는 direct child가 아니다" not in output
    assert "Legacy Child" not in output


def test_resume_skill_reads_project_local_state_db_for_child_context(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    codex_home = project / ".codex"
    state_db = codex_home / "state_5.sqlite"
    state_db.parent.mkdir(parents=True)
    conn = sqlite3.connect(state_db)
    try:
        conn.execute(
            "CREATE TABLE thread_spawn_edges ("
            "parent_thread_id TEXT, "
            "child_thread_id TEXT, "
            "status TEXT)"
        )
        conn.execute(
            "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
            ("parent12-session", "child123-session", "completed"),
        )
        conn.commit()
    finally:
        conn.close()

    parent = codex_home / "session-memory" / "threads" / "parent12-session"
    parent_contexts = parent / "contexts"
    parent_contexts.mkdir(parents=True)
    (parent / "INDEX.md").write_text(
        "---\nthread_id: parent12-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Parent\n\n## 컨텍스트 목록\n\n- [CONTEXT-parent.md] — parent\n",
        encoding="utf-8",
    )
    (parent_contexts / "CONTEXT-parent.md").write_text(
        "# Parent\n\n## 다음\nparent sqlite resume를 계속한다.\n",
        encoding="utf-8",
    )

    child = codex_home / "session-memory" / "threads" / "child123-session"
    child_contexts = child / "contexts"
    child_contexts.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nthread_id: child123-session\nlast_updated: 2026-05-04T00:05:00Z\n---\n\n"
        "# Child\n\n## 컨텍스트 목록\n\n- [CONTEXT-child.md] — child\n",
        encoding="utf-8",
    )
    (child_contexts / "CONTEXT-child.md").write_text(
        "# Child\n\n## 다음\nproject-local sqlite child context를 포함한다.\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "parent12"]) == 0
    output = capsys.readouterr().out
    assert "parent sqlite resume를 계속한다" in output
    assert "project-local sqlite child context를 포함한다" in output


def test_resume_skill_uses_current_artifact_when_graph_unavailable(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    session = project / ".codex" / "session-memory" / "threads" / "solo1234-session"
    contexts = session / "contexts"
    contexts.mkdir(parents=True)
    (session / "INDEX.md").write_text(
        "---\nthread_id: solo1234-session\nlast_updated: 2026-05-04T00:00:00Z\n---\n\n"
        "# Solo\n\n## 컨텍스트 목록\n\n- [CONTEXT-solo.md] — solo\n",
        encoding="utf-8",
    )
    (contexts / "CONTEXT-solo.md").write_text(
        "# Solo\n\n## 다음\ngraph 없이 현재 context만 사용한다.\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()
    real_loader = resume_skill.load_script_module

    def fake_loader(filename, module_name):
        if filename == "graph_store.py":
            raise RuntimeError("graph unavailable")
        return real_loader(filename, module_name)

    monkeypatch.setattr(resume_skill, "load_script_module", fake_loader)

    assert resume_skill.main(["resume.py", "solo1234"]) == 0
    output = capsys.readouterr().out
    assert "graph 없이 현재 context만 사용한다" in output
    assert "related:" not in output


def test_resume_skill_falls_back_to_legacy_sessions_without_flat_root(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    legacy_session = project / ".codex" / "sessions" / "legacy99-session"
    legacy_session.mkdir(parents=True)
    (legacy_session / "INDEX.md").write_text(
        "---\nsession_id: legacy99-session\nlast_updated: 2026-05-05T00:00:00Z\n---\n\n"
        "# Legacy\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py"]) == 0
    output = capsys.readouterr().out
    assert "legacy99" in output


def test_resume_skill_rejects_non_8_character_prefix(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    (project / ".codex" / "sessions").mkdir(parents=True)
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "abc123"]) == 2
    assert "exactly 8 characters" in capsys.readouterr().err


def test_resume_skill_rejects_ambiguous_prefix(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    for session_id, updated in [
        ("abc12345-one", "2026-05-02T00:00:00Z"),
        ("abc12345-two", "2026-05-03T00:00:00Z"),
    ]:
        session = project / ".codex" / "sessions" / session_id
        session.mkdir(parents=True)
        (session / "INDEX.md").write_text(
            f"---\nsession_id: {session_id}\nlast_updated: {updated}\n---\n\n"
            "# 세션 요약\n\n## 컨텍스트 목록\n\n",
            encoding="utf-8",
        )
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "abc12345"]) == 2
    assert "multiple sessions match" in capsys.readouterr().err


def test_resume_skill_matches_sessions_beyond_display_limit(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    sessions_root = project / ".codex" / "sessions"
    for index in range(12):
        session_id = f"recent{index:02d}-session"
        session = sessions_root / session_id
        session.mkdir(parents=True)
        (session / "INDEX.md").write_text(
            f"---\nsession_id: {session_id}\nlast_updated: 2026-05-03T00:{index:02d}:00Z\n---\n\n"
            "# 세션 요약\n\n## 컨텍스트 목록\n\n",
            encoding="utf-8",
        )
    target = sessions_root / "target99-session"
    contexts = target / "contexts"
    contexts.mkdir(parents=True)
    (target / "INDEX.md").write_text(
        "---\nsession_id: target99-session\nlast_updated: 2026-05-02T00:00:00Z\n---\n\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n- [CONTEXT-1.md] — older target\n",
        encoding="utf-8",
    )
    (contexts / "CONTEXT-1.md").write_text("# Target\n\n## 다음\n오래된 세션도 prefix로 찾는다.\n", encoding="utf-8")
    monkeypatch.setenv("CODEX_PROJECT_DIR", str(project))
    monkeypatch.chdir(project)

    resume_skill = load_resume_skill()

    assert resume_skill.main(["resume.py", "target99"]) == 0
    assert "오래된 세션도 prefix로 찾는다" in capsys.readouterr().out
