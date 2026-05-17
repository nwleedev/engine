import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PLUGIN_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "plugin-sources"
    / "session-memory"
    / "adapters"
    / "codex"
)
STATUS = PLUGIN_SOURCE / "skills" / "status" / "status.py"


@pytest.fixture(autouse=True)
def isolate_default_codex_home(monkeypatch, tmp_path):
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path / "home-without-codex"))


def load_status():
    module_name = "test_codex_session_memory_status"
    spec = importlib.util.spec_from_file_location(module_name, STATUS)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def configure_status_common(monkeypatch, status, tmp_path, session_id):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", session_id)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))
    monkeypatch.setattr(
        status.csm_agents_rules,
        "check_agents_rules",
        lambda root: SimpleNamespace(status="installed", missing=()),
    )


def write_artifact_index(tmp_path, session_id, *, last_updated="flat-current", last_offset=0):
    session_dir = tmp_path / ".codex" / "session-memory" / "threads" / session_id
    contexts = session_dir / "contexts"
    contexts.mkdir(parents=True)
    (contexts / "CONTEXT-20260502-1200-test.md").write_text("# test\n", encoding="utf-8")
    (session_dir / "INDEX.md").write_text(
        "---\n"
        f"last_updated: {last_updated}\n"
        f"last_processed_offset: {last_offset}\n"
        f"session_id: {session_id}\n"
        "---\n\n"
        "# Flat\n",
        encoding="utf-8",
    )
    return session_dir


def test_status_without_session_id_reports_diagnostic_without_internal_discovery(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CODEX_SESSION_ID", raising=False)
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "CODEX_SESSION_ID: not set" in output
    assert "CODEX_THREAD_ID" not in output
    assert "Graph:" not in output
    assert "Child sessions:" not in output


def test_status_reports_codex_session_id_artifact_only(monkeypatch, tmp_path, capsys):
    status = load_status()
    artifact_dir = write_artifact_index(
        tmp_path,
        "target-session",
        last_updated="2026-05-02T00:00:00Z",
        last_offset=42,
    )
    legacy_dir = tmp_path / ".codex" / "sessions" / "target-session"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "INDEX.md").write_text(
        "---\nlast_updated: legacy-stale\nlast_processed_offset: 1\n---\n\n# Legacy\n",
        encoding="utf-8",
    )
    configure_status_common(monkeypatch, status, tmp_path, "target-session")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert f"Project root: {tmp_path}" in output
    assert "Session id: target-session" in output
    assert f"Artifact path: {artifact_dir}" in output
    assert "Context files: 1" in output
    assert "Last saved: 2026-05-02T00:00:00Z" in output
    assert "Pending offset: 42" in output
    assert "AGENTS.md rules: installed" in output
    assert "legacy-stale" not in output
    assert "JSONL path:" not in output
    assert "Graph:" not in output
    assert "Child sessions:" not in output


def test_status_reports_orphan_contexts_for_artifact_repair(monkeypatch, tmp_path, capsys):
    status = load_status()
    artifact_dir = write_artifact_index(tmp_path, "target-session")
    contexts = artifact_dir / "contexts"
    (contexts / "CONTEXT-20260502-1200-test.md").unlink()
    (contexts / "CONTEXT-indexed.md").write_text("# Indexed\n", encoding="utf-8")
    (contexts / "CONTEXT-orphan.md").write_text("# Orphan\n", encoding="utf-8")
    (artifact_dir / "INDEX.md").write_text(
        "---\nsession_id: target-session\nlast_processed_offset: 0\n---\n\n"
        "## Contexts\n\n"
        "- [CONTEXT-indexed.md] — indexed\n",
        encoding="utf-8",
    )
    configure_status_common(monkeypatch, status, tmp_path, "target-session")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Orphan contexts: 1" in output
    assert "CONTEXT-orphan.md" in output
    assert "Repair: add missing context entries to INDEX.md" in output
    assert "CONTEXT-indexed.md" not in output


def test_status_missing_artifact_reports_clear_diagnostic_without_legacy_fallback(
    monkeypatch, tmp_path, capsys
):
    status = load_status()
    legacy_dir = tmp_path / ".codex" / "sessions" / "missing-session"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "INDEX.md").write_text(
        "---\nlast_updated: legacy-only\nlast_processed_offset: 1\n---\n\n# Legacy\n",
        encoding="utf-8",
    )
    configure_status_common(monkeypatch, status, tmp_path, "missing-session")

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "Session id: missing-session" in output
    assert ".codex/session-memory/threads/missing-session/INDEX.md" in output
    assert "status: not yet checkpointed" in output
    assert "legacy-only" not in output
    assert "Graph:" not in output
    assert "Child sessions:" not in output


def test_status_does_not_load_internal_graph_or_jsonl_helpers(monkeypatch):
    loaded = []
    original_spec_from_file_location = importlib.util.spec_from_file_location

    def fake_spec_from_file_location(module_name, module_path):
        loaded.append(Path(module_path).name)
        return original_spec_from_file_location(module_name, module_path)

    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)
    status = load_status()

    assert status is not None
    assert "graph_store.py" not in loaded
    assert "parent_locator.py" not in loaded
    assert "jsonl_parser.py" not in loaded


def test_status_uses_real_partial_agents_rules_report(monkeypatch, tmp_path, capsys):
    status = load_status()
    write_artifact_index(tmp_path, "abc123")
    (tmp_path / "AGENTS.md").write_text(
        "# Project Rules\n\n"
        "$session-memory:checkpoint\n"
        "$session-memory:status\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CODEX_SESSION_ID", "abc123")
    monkeypatch.setattr(status.csm_dotenv_loader, "load_project_dotenv", lambda cwd: None)
    monkeypatch.setattr(status.csm_project_root, "find_project_root", lambda cwd: str(tmp_path))

    assert status.main() == 0

    output = capsys.readouterr().out
    assert "AGENTS.md rules: partial" in output
    assert "$session-memory:resume" in output
    assert "CODEX_THREAD_ID" in output
    assert "$session-memory:checkpoint" not in output
    assert "$session-memory:status" not in output
