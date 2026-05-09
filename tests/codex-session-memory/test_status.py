import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
STATUS = PLUGIN / "skills" / "status" / "status.py"


def load_status():
    module_name = "test_codex_session_memory_status"
    spec = importlib.util.spec_from_file_location(module_name, STATUS)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_status_prints_checkpointed_session_fields(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True)
    (contexts_dir / "CONTEXT-20260502-1200-test.md").write_text("# test\n")
    index_path = session_dir / "INDEX.md"
    index_path.write_text("---\nlast_updated: 2026-05-02T00:00:00Z\nlast_processed_offset: 42\n---\n")
    child = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child.mkdir(parents=True)
    (child / "INDEX.md").write_text(
        "---\nrole: child\nparent_session_id: abc123\n---\n\n# Child\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-test-abc123.jsonl"
    jsonl_path.write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    def fake_read_frontmatter(path):
        if "child123" in str(path):
            return {"role": "child", "parent_session_id": "abc123"}
        return {"last_updated": "2026-05-02T00:00:00Z", "last_processed_offset": 42}

    monkeypatch.setattr(status.csm_index_io, "read_frontmatter", fake_read_frontmatter)
    monkeypatch.setattr(status.csm_jsonl_parser, "extract_delta", lambda path, offset: ([{"role": "user"}], 84))
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Project root: {tmp_path}" in output
    assert "Thread id: abc123" in output
    assert f"JSONL path: {jsonl_path}" in output
    assert "Context files: 1" in output
    assert "Last saved: 2026-05-02T00:00:00Z" in output
    assert "Pending offset: 42" in output
    assert "AGENTS.md rules: installed" in output
    assert "Hooks:" not in output
    assert "Child sessions: 1" in output
    assert "pending_turns: 1" in output


@pytest.mark.parametrize(("children_present", "expected_count"), ((False, 0), (True, 1)))
def test_status_child_count_is_stable_when_children_dir_absent_or_present(
    monkeypatch, tmp_path, capsys, children_present, expected_count
):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    session_dir.mkdir(parents=True)
    (session_dir / "INDEX.md").write_text(
        "---\nlast_updated: 2026-05-02T00:00:00Z\nlast_processed_offset: 0\n---\n",
        encoding="utf-8",
    )
    if children_present:
        child = tmp_path / ".codex" / "sessions" / "_children" / "child123"
        child.mkdir(parents=True)
        (child / "INDEX.md").write_text(
            "---\nrole: child\nparent_session_id: abc123\n---\n\n# Child\n",
            encoding="utf-8",
        )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Child sessions: {expected_count}" in output


def test_status_prints_child_parent_information(monkeypatch, tmp_path, capsys):
    status = load_status()
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert f"Parent INDEX.md: {parent_index.resolve()}" in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" not in output


def test_status_prefers_child_session_when_both_main_and_child_indexes_exist(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: child-current\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Current child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert "Last saved: child-current" in output
    assert "Last saved: main-stale" not in output


def test_status_reports_uncheckpointed_child_from_parent_evidence_before_stale_main(
    monkeypatch,
    tmp_path,
    capsys,
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(
            resolve_parent_thread_id=lambda thread_id, rollout_path=None, **kwargs: SimpleNamespace(
                role="child",
                parent_thread_id="parent123",
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert "Last saved: main-stale" not in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" in output


def test_status_reports_uncheckpointed_child_with_unknown_parent_before_stale_main(
    monkeypatch,
    tmp_path,
    capsys,
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    main_dir.mkdir(parents=True)
    (main_dir / "INDEX.md").write_text(
        "---\n"
        "last_updated: main-stale\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Stale main\n",
        encoding="utf-8",
    )
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(
            resolve_parent_thread_id=lambda thread_id, rollout_path=None, **kwargs: SimpleNamespace(
                role="child",
                parent_thread_id=None,
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: unknown" in output
    assert "Parent INDEX.md: missing" in output
    assert "Last saved: main-stale" not in output
    assert "Child sessions:" not in output
    assert "status: not yet checkpointed" in output


def test_status_passes_project_codex_home_to_parent_locator(monkeypatch, tmp_path):
    status = load_status()
    jsonl_path = tmp_path / "rollout-child123.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    calls = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    def resolve_parent_thread_id(thread_id, rollout_path=None, codex_home=None):
        calls.append((thread_id, rollout_path, codex_home))
        return SimpleNamespace(role="main", parent_thread_id=None)

    monkeypatch.setattr(
        status,
        "csm_parent_locator",
        SimpleNamespace(resolve_parent_thread_id=resolve_parent_thread_id),
        raising=False,
    )

    assert status.main() == 0

    assert calls == [("child123", jsonl_path, tmp_path / ".codex")]


def test_status_old_data_session_dir_signature_still_finds_child_session(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    main_dir = tmp_path / ".codex" / "sessions" / "child123"
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    def old_data_session_dir(root, thread_id):
        return main_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", old_data_session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Role: child" in output
    assert "Parent session: parent123" in output
    assert f"Parent INDEX.md: {parent_index.resolve()}" in output
    assert "status: not yet checkpointed" not in output


def test_status_data_session_dir_internal_type_error_is_not_swallowed(monkeypatch, tmp_path):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    def broken_data_session_dir(root, thread_id, role=None):
        if role is not None:
            raise TypeError("internal bug")
        return session_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", broken_data_session_dir)

    with pytest.raises(TypeError, match="internal bug"):
        status.main()


def test_status_parent_index_path_falls_back_without_parent_session_dir(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    child_dir = tmp_path / ".codex" / "sessions" / "_children" / "child123"
    child_dir.mkdir(parents=True)
    (child_dir / "INDEX.md").write_text(
        "---\n"
        "role: child\n"
        "parent_session_id: parent123\n"
        "last_updated: 2026-05-02T00:00:00Z\n"
        "last_processed_offset: 0\n"
        "---\n\n"
        "# Child\n",
        encoding="utf-8",
    )
    parent_index = tmp_path / ".codex" / "sessions" / "parent123" / "INDEX.md"
    parent_index.parent.mkdir(parents=True)
    parent_index.write_text("# Parent\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delattr(status.csm_session_locator, "parent_session_dir")
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "child123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Parent INDEX.md: {parent_index}" in output


@pytest.mark.parametrize(
    ("rules_status", "missing_markers"),
    (
        ("partial", ("CODEX_THREAD_ID", ".codex/")),
        ("missing", ("$codex-session-memory:checkpoint", "CODEX_THREAD_ID", ".codex/")),
    ),
)
def test_status_prints_missing_values_before_checkpoint(
    monkeypatch, tmp_path, capsys, rules_status, missing_markers
):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status=rules_status, missing=missing_markers),
    )

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "JSONL path: missing" in output
    assert "Context files: 0" in output
    assert "Last saved: never" in output
    assert "Pending offset: 0" in output
    assert f"AGENTS.md rules: {rules_status}" in output
    assert f"AGENTS.md missing markers: {', '.join(missing_markers)}" in output
    assert "Hooks:" not in output
    assert "status: not yet checkpointed" in output


def test_status_uses_real_partial_agents_rules_report(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"
    (tmp_path / "AGENTS.md").write_text(
        "# Project Rules\n\n"
        "$codex-session-memory:checkpoint\n"
        "$codex-session-memory:status\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "AGENTS.md rules: partial" in output
    assert "$codex-session-memory:resume" in output
    assert "CODEX_THREAD_ID" in output
    assert "$codex-session-memory:checkpoint" not in output
    assert "$codex-session-memory:status" not in output
    assert "Hooks:" not in output


def test_status_uses_real_not_found_agents_rules_report(monkeypatch, tmp_path, capsys):
    status = load_status()
    session_dir = tmp_path / ".codex" / "sessions" / "abc123"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "AGENTS.md rules: not found" in output
    assert "AGENTS.md missing markers:" in output
    assert "$codex-session-memory:checkpoint" in output
    assert "Hooks:" not in output


def test_status_without_thread_id_returns_zero(monkeypatch, tmp_path, capsys):
    status = load_status()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "CODEX_THREAD_ID: not set" in output
    assert "Hooks:" not in output
