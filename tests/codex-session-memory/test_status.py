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
    jsonl_path = tmp_path / "rollout-test-abc123.jsonl"
    jsonl_path.write_text("")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_session_locator, "current_thread_id", lambda: "abc123")
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(status.csm_session_locator, "data_session_dir", lambda root, thread_id: session_dir)
    monkeypatch.setattr(status.csm_session_locator, "find_jsonl_by_thread", lambda thread_id: jsonl_path)
    monkeypatch.setattr(
        status.csm_index_io,
        "read_frontmatter",
        lambda path: {"last_updated": "2026-05-02T00:00:00Z", "last_processed_offset": 42},
    )
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
    assert "pending_turns: 1" in output


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
