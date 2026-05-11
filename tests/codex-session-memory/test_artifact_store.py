import importlib.util
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"
ARTIFACT_STORE = SCRIPTS / "artifact_store.py"
INDEX_IO = SCRIPTS / "index_io.py"


def load_artifact_store():
    spec = importlib.util.spec_from_file_location("artifact_store", ARTIFACT_STORE)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_index_io():
    spec = importlib.util.spec_from_file_location("index_io_for_artifact_store_test", INDEX_IO)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_thread_artifact_dir_uses_flat_store(tmp_path):
    artifact_store = load_artifact_store()
    store = artifact_store.ArtifactStore(tmp_path)

    assert store.thread_dir("thread-1") == (
        tmp_path / ".codex" / "session-memory" / "threads" / "thread-1"
    )
    assert store.index_path("thread-1") == (
        tmp_path / ".codex" / "session-memory" / "threads" / "thread-1" / "INDEX.md"
    )


def test_legacy_discovery_finds_main_and_child_paths(tmp_path):
    artifact_store = load_artifact_store()
    main_index = tmp_path / ".codex" / "sessions" / "main-thread" / "INDEX.md"
    child_index = tmp_path / ".codex" / "sessions" / "_children" / "child-thread" / "INDEX.md"
    main_index.parent.mkdir(parents=True)
    child_index.parent.mkdir(parents=True)
    main_index.write_text("# Main\n", encoding="utf-8")
    child_index.write_text("# Child\n", encoding="utf-8")

    store = artifact_store.ArtifactStore(tmp_path)

    assert store.legacy_index_candidates("main-thread") == [main_index]
    assert store.legacy_index_candidates("child-thread") == [child_index]


def test_write_index_omits_relationship_source_fields(tmp_path):
    artifact_store = load_artifact_store()
    store = artifact_store.ArtifactStore(tmp_path)

    store.write_index(
        "thread-1",
        frontmatter={
            "thread_id": "thread-1",
            "artifact_schema_version": 2,
            "last_processed_offset": 10,
            "last_updated": "2026-05-11T00:00:00Z",
            "role": "child",
            "parent_session_id": "parent-1",
        },
        contexts=[{"filename": "CONTEXT-20260511-0000-checkpoint.md", "summary": "checkpoint"}],
    )

    text = store.index_path("thread-1").read_text(encoding="utf-8")
    assert "thread_id: thread-1" in text
    assert "artifact_schema_version: 2" in text
    assert "role:" not in text
    assert "parent_session_id:" not in text
    assert "- [CONTEXT-20260511-0000-checkpoint.md] — checkpoint" in text


def test_write_index_matches_index_io_output_after_relationship_field_cleanup(tmp_path):
    artifact_store = load_artifact_store()
    index_io = load_index_io()
    store = artifact_store.ArtifactStore(tmp_path)
    frontmatter = {
        "thread_id": "thread-1",
        "artifact_schema_version": 2,
        "last_processed_offset": 10,
        "role": "child",
        "parent_session_id": "parent-1",
    }
    contexts = [{"filename": "CONTEXT-first.md", "summary": "first"}]
    expected_path = tmp_path / "expected" / "INDEX.md"
    cleaned_frontmatter = {
        key: value
        for key, value in frontmatter.items()
        if key not in {"role", "parent_session_id"}
    }

    store.write_index("thread-1", frontmatter=frontmatter, contexts=contexts)
    index_io.write_index(expected_path, cleaned_frontmatter, contexts)

    assert store.index_path("thread-1").read_text(encoding="utf-8") == expected_path.read_text(
        encoding="utf-8"
    )


def test_write_index_is_compatible_with_index_io_context_append(tmp_path):
    artifact_store = load_artifact_store()
    index_io = load_index_io()
    store = artifact_store.ArtifactStore(tmp_path)

    store.write_index(
        "thread-1",
        frontmatter={
            "thread_id": "thread-1",
            "artifact_schema_version": 2,
            "last_processed_offset": 10,
        },
        contexts=[{"filename": "CONTEXT-first.md", "summary": "first"}],
    )

    index_io.append_context_entry(store.index_path("thread-1"), "CONTEXT-next.md", "next")

    text = store.index_path("thread-1").read_text(encoding="utf-8")
    assert text.count("## 컨텍스트 목록") == 1
    assert "## Contexts" not in text
    assert text.index("- [CONTEXT-first.md] — first") < text.index("- [CONTEXT-next.md] — next")
