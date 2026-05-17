import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "plugin-sources"
    / "session-memory"
    / "adapters"
    / "codex"
    / "scripts"
)
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


def test_context_filename_uses_timestamp_task_id_and_nonce(tmp_path):
    artifact_store = load_artifact_store()
    store = artifact_store.ArtifactStore(tmp_path)

    filename = store.context_filename(
        timestamp="20260517-101112",
        task_id="TASK 003/session memory",
        nonce="abc123",
    )

    assert filename == "CONTEXT-20260517-101112-task-003-session-memory-abc123.md"
    assert store.context_path("session-1", filename) == (
        tmp_path
        / ".codex"
        / "session-memory"
        / "threads"
        / "session-1"
        / "contexts"
        / filename
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
    assert text.count("## Contexts") == 1
    assert text.index("- [CONTEXT-first.md] — first") < text.index("- [CONTEXT-next.md] — next")


def test_atomic_append_context_entry_preserves_concurrent_reload(tmp_path):
    index_io = load_index_io()
    index_path = tmp_path / "INDEX.md"
    index_io.write_index(index_path, {"session_id": "session-1"}, [])

    index_io.append_context_entry(index_path, "CONTEXT-a.md", "first")
    index_io.append_context_entry(index_path, "CONTEXT-b.md", "second")

    text = index_path.read_text(encoding="utf-8")
    assert "- [CONTEXT-a.md] — first" in text
    assert "- [CONTEXT-b.md] — second" in text
    assert not list(tmp_path.glob("*.tmp"))


def test_first_checkpoint_append_creates_index_without_overwriting_prior_entry(tmp_path):
    index_io = load_index_io()
    index_path = tmp_path / "INDEX.md"

    index_io.append_context_entry_with_frontmatter(
        index_path,
        "CONTEXT-first.md",
        "first",
        writer_id="first",
        session_id="session-1",
        last_processed_offset=1,
    )
    index_io.append_context_entry_with_frontmatter(
        index_path,
        "CONTEXT-second.md",
        "second",
        writer_id="second",
        session_id="session-1",
        last_processed_offset=2,
    )

    text = index_path.read_text(encoding="utf-8")
    assert "- [CONTEXT-first.md] — first" in text
    assert "- [CONTEXT-second.md] — second" in text
    assert "last_processed_offset: 2" in text


def test_first_checkpoint_append_preserves_entries_from_concurrent_processes(tmp_path):
    index_path = tmp_path / "INDEX.md"
    worker = tmp_path / "append_worker.py"
    worker.write_text(
        "\n".join(
            [
                "import importlib.util",
                "import sys",
                "from pathlib import Path",
                f"module_path = Path({str(INDEX_IO)!r})",
                "spec = importlib.util.spec_from_file_location('index_io_worker', module_path)",
                "module = importlib.util.module_from_spec(spec)",
                "sys.modules[spec.name] = module",
                "spec.loader.exec_module(module)",
                "index_path = Path(sys.argv[1])",
                "filename = sys.argv[2]",
                "summary = sys.argv[3]",
                "module.append_context_entry_with_frontmatter(",
                "    index_path,",
                "    filename,",
                "    summary,",
                "    writer_id=summary,",
                "    session_id='session-1',",
                "    last_processed_offset=int(sys.argv[4]),",
                ")",
            ]
        ),
        encoding="utf-8",
    )

    processes = [
        subprocess.Popen(
            [
                sys.executable,
                str(worker),
                str(index_path),
                "CONTEXT-first.md",
                "first",
                "1",
            ]
        ),
        subprocess.Popen(
            [
                sys.executable,
                str(worker),
                str(index_path),
                "CONTEXT-second.md",
                "second",
                "2",
            ]
        ),
    ]
    for process in processes:
        assert process.wait(timeout=10) == 0

    text = index_path.read_text(encoding="utf-8")
    assert "- [CONTEXT-first.md] — first" in text
    assert "- [CONTEXT-second.md] — second" in text
    assert text.startswith("---\n")
    assert text.count("## Contexts") == 1


def test_atomic_write_uses_writer_scoped_backup_and_same_directory_temp(tmp_path, monkeypatch):
    index_io = load_index_io()
    index_path = tmp_path / "INDEX.md"
    index_path.write_text("old index\n", encoding="utf-8")
    captured = {}
    real_mkstemp = index_io.tempfile.mkstemp

    def capture_mkstemp(*, prefix, suffix, dir, text):
        captured["prefix"] = prefix
        captured["suffix"] = suffix
        captured["dir"] = Path(dir)
        return real_mkstemp(prefix=prefix, suffix=suffix, dir=dir, text=text)

    monkeypatch.setattr(index_io.tempfile, "mkstemp", capture_mkstemp)
    monkeypatch.setattr(index_io.os, "getpid", lambda: 12345)

    backup_path = index_io._atomic_write(index_path, "new index\n", writer_id="checkpoint-abc")

    assert index_path.read_text(encoding="utf-8") == "new index\n"
    assert backup_path == tmp_path / ".index.backup.checkpoint-abc.12345.md"
    assert backup_path.read_text(encoding="utf-8") == "old index\n"
    assert captured == {
        "prefix": ".index.tmp.checkpoint-abc.12345.",
        "suffix": ".md",
        "dir": tmp_path,
    }


def test_atomic_write_error_preserves_backup_path_when_replace_fails(tmp_path, monkeypatch):
    index_io = load_index_io()
    index_path = tmp_path / "INDEX.md"
    index_path.write_text("old index\n", encoding="utf-8")
    monkeypatch.setattr(index_io.os, "getpid", lambda: 12345)

    def fail_replace(*_args):
        raise OSError("replace failed")

    monkeypatch.setattr(index_io.os, "replace", fail_replace)

    try:
        index_io._atomic_write(index_path, "new index\n", writer_id="checkpoint-abc")
    except index_io.AtomicIndexWriteError as exc:
        assert exc.backup_path == tmp_path / ".index.backup.checkpoint-abc.12345.md"
        assert exc.backup_path.read_text(encoding="utf-8") == "old index\n"
    else:
        raise AssertionError("expected AtomicIndexWriteError")


def test_append_context_entry_with_frontmatter_updates_index_in_one_locked_render(
    tmp_path, monkeypatch
):
    index_io = load_index_io()
    index_path = tmp_path / "INDEX.md"
    index_io.write_index(index_path, {"session_id": "session-1", "last_processed_offset": 1}, [])
    calls = {"lock": 0, "render": 0}
    real_lock = index_io._index_lock
    real_render = index_io._render

    def count_lock(path):
        calls["lock"] += 1
        return real_lock(path)

    def count_render(frontmatter, body):
        calls["render"] += 1
        return real_render(frontmatter, body)

    monkeypatch.setattr(index_io, "_index_lock", count_lock)
    monkeypatch.setattr(index_io, "_render", count_render)
    monkeypatch.setattr(index_io.os, "getpid", lambda: 12345)

    backup_path = index_io.append_context_entry_with_frontmatter(
        index_path,
        "CONTEXT-next.md",
        "next",
        writer_id="checkpoint-abc",
        last_processed_offset=2,
        last_updated="2026-05-17T10:11:12Z",
    )

    text = index_path.read_text(encoding="utf-8")
    assert calls == {"lock": 1, "render": 1}
    assert backup_path == tmp_path / ".index.backup.checkpoint-abc.12345.md"
    assert "- [CONTEXT-next.md] — next" in text
    assert "last_processed_offset: 2" in text
    assert "last_updated: 2026-05-17T10:11:12Z" in text
