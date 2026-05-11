import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"
MIGRATE = SCRIPTS / "migrate_child_sessions.py"


def load_migrate_child_sessions():
    spec = importlib.util.spec_from_file_location("migrate_child_sessions", MIGRATE)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_session(root: Path, session_id: str, index_text: str = "# Session\n") -> Path:
    session_dir = root / ".codex" / "sessions" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "INDEX.md").write_text(index_text, encoding="utf-8")
    return session_dir


def write_legacy_child_session(
    root: Path,
    session_id: str,
    index_text: str = "# Session\n",
) -> Path:
    session_dir = root / ".codex" / "sessions" / "_children" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "INDEX.md").write_text(index_text, encoding="utf-8")
    return session_dir


def flat_destination(root: Path, session_id: str) -> Path:
    return root / ".codex" / "session-memory" / "threads" / session_id


def child_resolution(parent_thread_id: str | None = "parent-thread"):
    return SimpleNamespace(
        role="child",
        parent_thread_id=parent_thread_id,
        source="test",
        confidence="high",
        reason="test child evidence",
        warnings=(),
    )


def main_resolution():
    return SimpleNamespace(
        role="main",
        parent_thread_id=None,
        source="none",
        confidence="none",
        reason="test miss",
        warnings=(),
    )


def test_dry_run_prints_flat_destination_and_does_not_move(monkeypatch, tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    main_dir = write_session(tmp_path, "main-thread")
    child_dir = write_session(tmp_path, "top-level-child")
    write_session(tmp_path, "_children")
    write_session(tmp_path, ".hidden")
    legacy_child_dir = write_legacy_child_session(tmp_path, "children-child")
    calls = []

    def find_jsonl_by_thread(thread_id):
        return tmp_path / f"rollout-{thread_id}.jsonl"

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", find_jsonl_by_thread)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        calls.append((thread_id, rollout_path))
        if thread_id == "main-thread":
            return main_resolution()
        return child_resolution("parent-thread")

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "DRY-RUN main-thread -> session-memory/threads/main-thread parent=none" in output
    assert (
        "DRY-RUN top-level-child -> session-memory/threads/top-level-child "
        "parent=parent-thread"
    ) in output
    assert (
        "DRY-RUN children-child -> session-memory/threads/children-child "
        "parent=parent-thread"
    ) in output
    assert main_dir.is_dir()
    assert child_dir.is_dir()
    assert legacy_child_dir.is_dir()
    assert not flat_destination(tmp_path, "main-thread").exists()
    assert not flat_destination(tmp_path, "top-level-child").exists()
    assert not flat_destination(tmp_path, "children-child").exists()
    assert calls == [
        ("children-child", tmp_path / "rollout-children-child.jsonl"),
        ("main-thread", tmp_path / "rollout-main-thread.jsonl"),
        ("top-level-child", tmp_path / "rollout-top-level-child.jsonl"),
    ]


def test_apply_moves_top_level_child_and_parent_main_to_flat_destinations(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(tmp_path, "child-thread", "# Child\n")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Child\n"
    assert not parent_dir.exists()
    assert (
        flat_destination(tmp_path, "parent-thread") / "INDEX.md"
    ).read_text(encoding="utf-8") == original_parent_index


def test_apply_moves_legacy_children_child_to_flat_destination(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    child_dir = write_legacy_child_session(tmp_path, "child-thread", "# Legacy Child\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Legacy Child\n"


def test_apply_cleans_child_frontmatter_parent_when_parent_locator_misses(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    child_index = (
        "---\n"
        "thread_id: child-thread\n"
        "role: child\n"
        "parent_session_id: parent-thread\n"
        "summary: keep me\n"
        "---\n\n"
        "# Child\n"
        "\n"
        "Body stays.\n"
    )
    expected_child_index = (
        "---\n"
        "thread_id: child-thread\n"
        "summary: keep me\n"
        "---\n\n"
        "# Child\n"
        "\n"
        "Body stays.\n"
    )
    child_dir = write_session(tmp_path, "child-thread", child_index)
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: main_resolution(),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == expected_child_index
    assert not parent_dir.exists()
    assert (
        flat_destination(tmp_path, "parent-thread") / "INDEX.md"
    ).read_text(encoding="utf-8") == original_parent_index


def test_migration_passes_project_codex_home_to_parent_locator(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-thread", "# Child\n")
    calls = []

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, codex_home=None):
        calls.append((thread_id, rollout_path, codex_home))
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path)]) == 0

    assert calls == [("child-thread", None, tmp_path / ".codex")]


def test_apply_reads_parent_from_project_state_db_and_moves_parent_main(tmp_path):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(tmp_path, "child-thread", "# Child\n")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    db = tmp_path / ".codex" / "state_5.sqlite"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE thread_spawn_edges ("
        "parent_thread_id TEXT NOT NULL, "
        "child_thread_id TEXT NOT NULL PRIMARY KEY, "
        "status TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE threads ("
        "id TEXT PRIMARY KEY, "
        "rollout_path TEXT NOT NULL, "
        "source TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-thread", "child-thread", "open"),
    )
    conn.commit()
    conn.close()

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Child\n"
    assert not parent_dir.exists()
    assert (
        flat_destination(tmp_path, "parent-thread") / "INDEX.md"
    ).read_text(encoding="utf-8") == original_parent_index


def test_apply_does_not_add_relationship_frontmatter(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    original_child_index = "# Legacy child\n"
    write_session(tmp_path, "child-thread", original_child_index)
    write_session(tmp_path, "parent-thread", "# Parent\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    child_index = (flat_destination(tmp_path, "child-thread") / "INDEX.md").read_text(
        encoding="utf-8"
    )
    assert child_index == original_child_index
    assert "role: child" not in child_index
    assert "parent_session_id: parent-thread" not in child_index


def test_apply_moves_legacy_main_to_flat_destination(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    main_dir = write_session(tmp_path, "main-thread", "# Main\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: main_resolution(),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "main-thread")
    assert not main_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Main\n"


def test_flat_destination_conflict_returns_2_and_leaves_source_and_parent_intact(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    source = write_session(tmp_path, "child-thread", "# Source\n")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    destination = flat_destination(tmp_path, "child-thread")
    destination.mkdir(parents=True)
    (destination / "INDEX.md").write_text("# Existing\n", encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "CONFLICT child-thread" in captured.err
    assert "CONFLICT" not in captured.out
    assert source.is_dir()
    assert (source / "INDEX.md").read_text(encoding="utf-8") == "# Source\n"
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Existing\n"
    assert (parent_dir / "INDEX.md").read_text(encoding="utf-8") == original_parent_index


def test_apply_preflights_all_flat_conflicts_before_moving_any_candidate(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    conflict_destination = flat_destination(tmp_path, "child-b")
    conflict_destination.mkdir(parents=True)
    (conflict_destination / "INDEX.md").write_text("# Existing B\n", encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "CONFLICT child-b" in captured.err
    assert "CONFLICT" not in captured.out
    assert first_source.is_dir()
    assert second_source.is_dir()
    assert not flat_destination(tmp_path, "child-a").exists()
    assert (conflict_destination / "INDEX.md").read_text(encoding="utf-8") == "# Existing B\n"


def test_apply_preflights_duplicate_flat_destinations_before_moving(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    top_level_source = write_session(tmp_path, "child-thread", "# Top-level\n")
    legacy_source = write_legacy_child_session(tmp_path, "child-thread", "# Legacy\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "CONFLICT child-thread" in captured.err
    assert "CONFLICT" not in captured.out
    assert top_level_source.is_dir()
    assert legacy_source.is_dir()
    assert not flat_destination(tmp_path, "child-thread").exists()


def test_apply_removes_legacy_children_link_without_adding_child_sessions(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    write_legacy_child_session(tmp_path, "child-thread")
    existing_link = "- [child-th](../_children/child-thread/INDEX.md) - migrated child session"
    parent_dir = write_session(
        tmp_path,
        "parent-thread",
        "# Parent\n\nIntro\n" + existing_link + "\nOutro\n",
    )

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    assert not parent_dir.exists()
    parent_index = (flat_destination(tmp_path, "parent-thread") / "INDEX.md").read_text(
        encoding="utf-8"
    )
    assert parent_index == "# Parent\n\nIntro\nOutro\n"
    assert "../_children/child-thread/INDEX.md" not in parent_index
    assert "Child Sessions" not in parent_index


def test_apply_preserves_parent_note_text_around_legacy_children_link(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    write_legacy_child_session(tmp_path, "child-thread")
    parent_dir = write_session(
        tmp_path,
        "parent-thread",
        (
            "# Parent\n\n"
            "reviewer note before [child](../_children/child-thread/INDEX.md) "
            "reviewer note after\n"
        ),
    )

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    assert not parent_dir.exists()
    parent_index = (flat_destination(tmp_path, "parent-thread") / "INDEX.md").read_text(
        encoding="utf-8"
    )
    assert parent_index == "# Parent\n\nreviewer note before  reviewer note after\n"
    assert "../_children/child-thread/INDEX.md" not in parent_index


def test_apply_rolls_back_moved_directory_when_normalize_write_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    child_index = (
        "---\n"
        "thread_id: child-thread\n"
        "role: child\n"
        "parent_session_id: parent-thread\n"
        "---\n\n"
        "# Child\n"
    )
    source = write_session(tmp_path, "child-thread", child_index)

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    def fail_atomic_write(path, text):
        raise OSError("normalize write failed")

    monkeypatch.setattr(migrate, "_write_text_atomically", fail_atomic_write, raising=False)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR normalizing migrated INDEX.md for child-thread" in captured.err
    assert source.is_dir()
    assert (source / "INDEX.md").read_text(encoding="utf-8") == child_index
    assert not flat_destination(tmp_path, "child-thread").exists()
    assert not (tmp_path / ".codex" / "session-memory" / "threads").exists()


def test_apply_rolls_back_normalized_child_when_parent_cleanup_write_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    child_index = (
        "---\n"
        "thread_id: child-thread\n"
        "role: child\n"
        "parent_session_id: parent-thread\n"
        "---\n\n"
        "# Child\n"
    )
    parent_index = (
        "# Parent\n\n"
        "- [child-th](../_children/child-thread/INDEX.md) - migrated child session\n"
    )
    child_source = write_legacy_child_session(tmp_path, "child-thread", child_index)
    parent_source = write_session(tmp_path, "parent-thread", parent_index)

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    original_atomic_write = migrate._write_text_atomically

    def fail_parent_cleanup_write(path, text):
        if path.parent.name == "parent-thread":
            raise OSError("parent cleanup write failed")
        original_atomic_write(path, text)

    monkeypatch.setattr(migrate, "_write_text_atomically", fail_parent_cleanup_write)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR cleaning parent INDEX.md for parent-thread" in captured.err
    assert child_source.is_dir()
    assert (child_source / "INDEX.md").read_text(encoding="utf-8") == child_index
    assert parent_source.is_dir()
    assert (parent_source / "INDEX.md").read_text(encoding="utf-8") == parent_index
    assert not flat_destination(tmp_path, "child-thread").exists()
    assert not flat_destination(tmp_path, "parent-thread").exists()


def test_apply_rolls_back_mixed_sources_when_parent_cleanup_write_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    legacy_source = write_legacy_child_session(tmp_path, "children-child", "# Legacy\n")
    top_level_source = write_session(tmp_path, "top-level-child", "# Top Level\n")
    parent_index = (
        "# Parent\n\n"
        "- [legacy](../_children/children-child/INDEX.md) - migrated child session\n"
        "- [top](../_children/top-level-child/INDEX.md) - migrated child session\n"
    )
    parent_source = write_session(tmp_path, "parent-thread", parent_index)

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id in {"children-child", "top-level-child"}:
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    original_atomic_write = migrate._write_text_atomically

    def fail_parent_cleanup_write(path, text):
        if path.parent.name == "parent-thread":
            raise OSError("parent cleanup write failed")
        original_atomic_write(path, text)

    monkeypatch.setattr(migrate, "_write_text_atomically", fail_parent_cleanup_write)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR cleaning parent INDEX.md for parent-thread" in captured.err
    assert legacy_source.is_dir()
    assert top_level_source.is_dir()
    assert parent_source.is_dir()
    assert (parent_source / "INDEX.md").read_text(encoding="utf-8") == parent_index
    assert not flat_destination(tmp_path, "children-child").exists()
    assert not flat_destination(tmp_path, "top-level-child").exists()
    assert not flat_destination(tmp_path, "parent-thread").exists()


def test_apply_reports_manual_cleanup_when_backup_restore_write_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    child_index = "# Child\n"
    parent_index = (
        "# Parent\n\n"
        "- [child-th](../_children/child-thread/INDEX.md) - migrated child session\n"
    )
    write_legacy_child_session(tmp_path, "child-thread", child_index)
    write_session(tmp_path, "parent-thread", parent_index)
    restore_should_fail = False

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None, **kwargs):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    original_atomic_write = migrate._write_text_atomically

    def fail_parent_cleanup_after_partial_write(path, text):
        nonlocal restore_should_fail
        if path.parent.name == "parent-thread":
            if restore_should_fail:
                raise OSError("backup restore write failed")
            original_atomic_write(path, text)
            restore_should_fail = True
            raise OSError("parent cleanup write failed")
        original_atomic_write(path, text)

    monkeypatch.setattr(migrate, "_write_text_atomically", fail_parent_cleanup_after_partial_write)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR rollback failed" in captured.err
    assert "MANUAL CLEANUP REQUIRED" in captured.err
    assert "MOVED" not in captured.out


def test_apply_rolls_back_successful_moves_when_later_move_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    original_move = migrate.shutil.move
    move_calls = []

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    def fail_second_child_move(source, destination):
        move_calls.append((Path(source).name, Path(destination).name))
        if Path(source).name == "child-b":
            raise OSError("second move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ROLLBACK" in captured.err
    assert "MOVED" not in captured.out
    assert move_calls[:2] == [("child-a", "child-a"), ("child-b", "child-b")]
    assert first_source.is_dir()
    assert second_source.is_dir()
    assert not flat_destination(tmp_path, "child-a").exists()
    assert not flat_destination(tmp_path, "child-b").exists()
    assert not (tmp_path / ".codex" / "session-memory" / "threads").exists()


def test_apply_rolls_back_mixed_source_moves_when_later_top_level_move_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    legacy_source = write_legacy_child_session(tmp_path, "children-child", "# Children Child\n")
    top_level_source = write_session(tmp_path, "top-level-child", "# Top Level Child\n")
    original_move = migrate.shutil.move
    moved_order = []

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("parent-thread"),
    )

    def fail_top_level_move(source, destination):
        source_path = Path(source)
        moved_order.append(source_path.name)
        if source_path.name == "top-level-child":
            raise OSError("top-level move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_top_level_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ROLLBACK" in captured.err
    assert "MOVED" not in captured.out
    assert moved_order[:2] == ["children-child", "top-level-child"]
    assert legacy_source.is_dir()
    assert top_level_source.is_dir()
    assert not flat_destination(tmp_path, "children-child").exists()
    assert not flat_destination(tmp_path, "top-level-child").exists()
    assert not (tmp_path / ".codex" / "session-memory" / "threads").exists()


def test_apply_rolls_back_successful_moves_when_later_move_raises_shutil_error(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    original_move = migrate.shutil.move

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("missing-parent"),
    )

    def fail_second_child_move(source, destination):
        if Path(source).name == "child-b":
            raise migrate.shutil.Error("second move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR" in captured.err or "ROLLBACK" in captured.err
    assert "MOVED" not in captured.out
    assert first_source.is_dir()
    assert second_source.is_dir()
    assert not flat_destination(tmp_path, "child-a").exists()
    assert not flat_destination(tmp_path, "child-b").exists()


def test_apply_reports_shutil_error_when_rollback_move_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-a", "# Child A\n")
    write_session(tmp_path, "child-b", "# Child B\n")
    original_move = migrate.shutil.move

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("missing-parent"),
    )

    def fail_second_child_and_rollback_move(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.name == "child-b":
            raise OSError("second move failed")
        if (
            source_path.parent == tmp_path / ".codex" / "session-memory" / "threads"
            and destination_path.name == "child-a"
        ):
            raise migrate.shutil.Error("rollback move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_and_rollback_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR rollback failed" in captured.err
    assert "MANUAL CLEANUP REQUIRED" in captured.err
    assert str(flat_destination(tmp_path, "child-a")) in captured.err
    assert "MOVED" not in captured.out
    assert not (tmp_path / ".codex" / "sessions" / "child-a").exists()
    assert flat_destination(tmp_path, "child-a").is_dir()


def test_apply_preserves_preexisting_threads_root_when_apply_fails(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    threads_root = tmp_path / ".codex" / "session-memory" / "threads"
    threads_root.mkdir(parents=True)
    write_session(tmp_path, "child-a", "# Child A\n")
    write_session(tmp_path, "child-b", "# Child B\n")
    original_move = migrate.shutil.move

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None, **kwargs: child_resolution("missing-parent"),
    )

    def fail_second_child_move(source, destination):
        if Path(source).name == "child-b":
            raise migrate.shutil.Error("second move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    assert threads_root.is_dir()
