from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory"


def read_plugin_file(relative_path: str) -> str:
    return (PLUGIN / relative_path).read_text(encoding="utf-8")


def test_readmes_document_flat_migration_without_legacy_child_append():
    for relative_path in ("README.md", "README.ko.md"):
        text = read_plugin_file(relative_path)

        assert ".codex/session-memory/threads/<CODEX_THREAD_ID>/" in text
        assert ".codex/session-memory/threads/<id>/" in text
        assert "role" in text
        assert "parent_session_id" in text
        assert "Child Sessions" in text
        if relative_path == "README.md":
            assert "does not add new parent `Child Sessions` links" in text
        assert "Graph: unavailable" in text
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
    assert "unavailable" in checkpoint
    assert "source" in checkpoint
    assert "confidence" in checkpoint
    assert "reason" in checkpoint
    assert "warnings" in checkpoint
    assert "do not create new `_children` paths" in checkpoint
    assert "parent_locator" in checkpoint
    assert "graph_store" in checkpoint

    assert ".codex/session-memory/threads/<CODEX_THREAD_ID>/INDEX.md" in resume
    assert "If graph lookup is unavailable" in resume
    assert "role" in resume
    assert "parent_session_id" in resume

    assert ".codex/session-memory/threads/<CODEX_THREAD_ID>/" in status
    assert "Graph: unavailable" in status
    assert "parent_locator" in status
    assert "graph_store" in status
