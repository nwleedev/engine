from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory"


def read_plugin_file(relative_path: str) -> str:
    return (PLUGIN / relative_path).read_text(encoding="utf-8")


def test_readmes_document_flat_migration_without_legacy_child_append():
    for relative_path in ("README.md", "README.ko.md"):
        text = read_plugin_file(relative_path)

        assert ".codex/session-memory/threads/<CODEX_SESSION_ID>/" in text
        assert ".codex/session-memory/threads/<id>/" in text
        assert "role" in text
        assert "parent_session_id" in text
        assert "Child Sessions" in text
        if relative_path == "README.md":
            assert "does not add new parent `Child Sessions` links" in text
        assert "Artifact-only mode" in text
        assert "CODEX_SESSION_ID=<main-thread-id> codex resume <main-thread-id>" in text
        assert "output-only" in text
        assert "template must not be" in text or "Template를 그대로 저장하면" in text
        assert "executive_summary" in text
        assert "detailed_state" in text
        assert "graph_context" in text
        assert "rtk python tools/build_plugins.py" in text
        assert "rtk python tools/validate_generated.py" in text
        assert "moves resolvable child folders to `.codex/sessions/_children/`" not in text
        assert "appends parent `Child Sessions`" not in text


def test_skills_document_graph_first_degraded_mode():
    checkpoint = read_plugin_file("skills/checkpoint/SKILL.md")
    resume = read_plugin_file("skills/resume/SKILL.md")
    status = read_plugin_file("skills/status/SKILL.md")

    assert "9-section CONTEXT" in checkpoint
    assert "CODEX_SESSION_ID" in checkpoint
    assert "`CODEX_THREAD_ID` is used only to locate the active rollout JSONL" in checkpoint
    assert "contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md" in checkpoint
    assert "Mandatory Active Codex Actions" in checkpoint
    assert "do not stop or report completion" in checkpoint
    assert "required structure, not a completed artifact" in checkpoint
    assert "active Codex's responsibility" in checkpoint
    assert "Do not refuse or stop" in checkpoint
    assert "guidance:" in checkpoint
    assert "<title>" in checkpoint
    assert "<summary>" in checkpoint
    assert "checkpoint is not complete" in checkpoint
    assert "parent_locator" in checkpoint
    assert "graph_store" in checkpoint

    assert ".codex/session-memory/threads/<CODEX_SESSION_ID>/INDEX.md" in resume
    assert "CODEX_SESSION_ID" in resume
    assert "does not use Codex graph state" in resume

    assert "artifact-only session-memory status for CODEX_SESSION_ID" in status
    assert "does not inspect" in status
    assert "parent locators" in status
