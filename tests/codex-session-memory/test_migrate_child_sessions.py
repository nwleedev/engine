import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"
MIGRATE = SCRIPTS / "migrate_child_sessions.py"


def load_migrate_child_sessions():
    spec = importlib.util.spec_from_file_location("migrate_child_sessions", MIGRATE)
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


def test_dry_run_prints_candidate_and_does_not_move(monkeypatch, tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(tmp_path, "child-thread")
    write_session(tmp_path, "_children")
    write_session(tmp_path, ".hidden")
    rollout = tmp_path / "rollout-child-thread.jsonl"
    calls = []

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: rollout)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        calls.append((thread_id, rollout_path))
        return child_resolution("parent-thread")

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path)]) == 0

    output = capsys.readouterr().out
    assert "DRY-RUN child-thread -> _children/child-thread parent=parent-thread" in output
    assert child_dir.is_dir()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-thread").exists()
    assert calls == [("child-thread", rollout)]


def test_apply_moves_candidate_and_appends_parent_link(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(tmp_path, "child-thread")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").is_file()
    parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "## Child Sessions" in parent_index
    assert "- [child-th](../_children/child-thread/INDEX.md) - migrated child session" in parent_index


def test_apply_moves_candidate_and_warns_when_parent_index_is_missing(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(tmp_path, "child-thread", "# Child\n")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None: child_resolution("missing-parent"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    captured = capsys.readouterr()
    destination = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Child\n"
    assert "WARNING parent INDEX.md missing for missing-parent" in captured.err
    assert "WARNING" not in captured.out


def test_parent_miss_or_child_without_parent_does_not_move(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    main_dir = write_session(tmp_path, "main-thread")
    child_without_parent_dir = write_session(tmp_path, "child-without-parent")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-without-parent":
            return child_resolution(None)
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    assert main_dir.is_dir()
    assert child_without_parent_dir.is_dir()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "main-thread").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-without-parent").exists()


def test_destination_conflict_returns_2_and_leaves_source_intact(monkeypatch, tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    source = write_session(tmp_path, "child-thread", "# Source\n")
    destination = tmp_path / ".codex" / "sessions" / "_children" / "child-thread"
    destination.mkdir(parents=True)
    (destination / "INDEX.md").write_text("# Existing\n", encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "CONFLICT child-thread" in captured.err
    assert "CONFLICT" not in captured.out
    assert source.is_dir()
    assert (source / "INDEX.md").read_text(encoding="utf-8") == "# Source\n"
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Existing\n"


def test_apply_preflights_all_conflicts_before_moving_any_candidate(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    conflict_destination = tmp_path / ".codex" / "sessions" / "_children" / "child-b"
    conflict_destination.mkdir(parents=True)
    (conflict_destination / "INDEX.md").write_text("# Existing B\n", encoding="utf-8")

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None: child_resolution("parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "CONFLICT child-b" in captured.err
    assert "CONFLICT" not in captured.out
    assert first_source.is_dir()
    assert second_source.is_dir()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-a").exists()
    assert (conflict_destination / "INDEX.md").read_text(encoding="utf-8") == "# Existing B\n"


def test_apply_does_not_duplicate_existing_parent_link(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-thread")
    existing_link = "- [child-th](../_children/child-thread/INDEX.md) - migrated child session"
    parent_dir = write_session(
        tmp_path,
        "parent-thread",
        "# Parent\n\n## Child Sessions\n\n" + existing_link + "\n",
    )

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    assert parent_index.count(existing_link) == 1


def test_apply_dedupes_parent_link_by_target_when_suffix_differs(monkeypatch, tmp_path):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-thread")
    existing_link = "- [child-th](../_children/child-thread/INDEX.md) — reviewer checkpoint"
    parent_dir = write_session(
        tmp_path,
        "parent-thread",
        "# Parent\n\n## Child Sessions\n\n" + existing_link + "\n",
    )

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    assert parent_index.count("../_children/child-thread/INDEX.md") == 1
    assert existing_link in parent_index


def test_apply_preflights_parent_index_update_failure_before_moving(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    source = write_session(tmp_path, "child-thread", "# Child\n")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    parent_index = parent_dir / "INDEX.md"
    original_read_text = migrate.Path.read_text

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-thread":
            return child_resolution("parent-thread")
        return main_resolution()

    def fail_parent_index_read(path, *args, **kwargs):
        if path == parent_index:
            raise OSError("cannot read parent index")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    monkeypatch.setattr(migrate.Path, "read_text", fail_parent_index_read)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    assert source.is_dir()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-thread").exists()


def test_apply_rolls_back_successful_moves_when_later_move_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_move = migrate.shutil.move
    move_calls = []

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None: child_resolution("parent-thread"),
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
    assert not (tmp_path / ".codex" / "sessions" / "_children").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-a").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-b").exists()
    parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "../_children/child-a/INDEX.md" not in parent_index
    assert "../_children/child-b/INDEX.md" not in parent_index


def test_apply_rolls_back_moves_and_parent_text_when_parent_write_fails_after_moves(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    first_source = write_session(tmp_path, "child-a", "# Child A\n")
    second_source = write_session(tmp_path, "child-b", "# Child B\n")
    first_parent = write_session(tmp_path, "parent-a", "# Parent A\n")
    second_parent = write_session(tmp_path, "parent-b", "# Parent B\n")
    first_parent_index = first_parent / "INDEX.md"
    second_parent_index = second_parent / "INDEX.md"
    first_parent_original = first_parent_index.read_text(encoding="utf-8")
    second_parent_original = second_parent_index.read_text(encoding="utf-8")
    original_write_text = migrate.Path.write_text

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-a":
            return child_resolution("parent-a")
        if thread_id == "child-b":
            return child_resolution("parent-b")
        return main_resolution()

    def fail_second_parent_write(path, text, *args, **kwargs):
        if path == second_parent_index:
            raise OSError("parent write failed")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    monkeypatch.setattr(migrate.Path, "write_text", fail_second_parent_write)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "MOVED" not in captured.out
    assert first_source.is_dir()
    assert second_source.is_dir()
    assert not (tmp_path / ".codex" / "sessions" / "_children").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-a").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-b").exists()
    assert first_parent_index.read_text(encoding="utf-8") == first_parent_original
    assert second_parent_index.read_text(encoding="utf-8") == second_parent_original


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
        lambda thread_id, rollout_path=None: child_resolution("missing-parent"),
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
    assert not (tmp_path / ".codex" / "sessions" / "_children").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-a").exists()
    assert not (tmp_path / ".codex" / "sessions" / "_children" / "child-b").exists()


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
        lambda thread_id, rollout_path=None: child_resolution("missing-parent"),
    )

    def fail_second_child_and_rollback_move(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.name == "child-b":
            raise OSError("second move failed")
        if source_path.parent.name == "_children" and destination_path.name == "child-a":
            raise migrate.shutil.Error("rollback move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_and_rollback_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "ERROR rollback failed" in captured.err
    assert "MANUAL CLEANUP REQUIRED" in captured.err
    assert str(tmp_path / ".codex" / "sessions" / "_children" / "child-a") in captured.err
    assert "MOVED" not in captured.out
    assert not (tmp_path / ".codex" / "sessions" / "child-a").exists()
    assert (tmp_path / ".codex" / "sessions" / "_children" / "child-a").is_dir()


def test_apply_reports_manual_cleanup_when_parent_restore_fails(
    monkeypatch,
    tmp_path,
    capsys,
):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-a", "# Child A\n")
    write_session(tmp_path, "child-b", "# Child B\n")
    first_parent = write_session(tmp_path, "parent-a", "# Parent A\n")
    second_parent = write_session(tmp_path, "parent-b", "# Parent B\n")
    first_parent_index = first_parent / "INDEX.md"
    second_parent_index = second_parent / "INDEX.md"
    original_write_text = migrate.Path.write_text
    write_counts = {}

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)

    def resolve_parent_thread_id(thread_id, rollout_path=None):
        if thread_id == "child-a":
            return child_resolution("parent-a")
        if thread_id == "child-b":
            return child_resolution("parent-b")
        return main_resolution()

    def fail_second_parent_write_and_first_restore(path, text, *args, **kwargs):
        write_counts[path] = write_counts.get(path, 0) + 1
        if path == second_parent_index:
            raise OSError("parent write failed")
        if path == first_parent_index and write_counts[path] == 2:
            raise OSError("parent restore failed")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(migrate.pl, "resolve_parent_thread_id", resolve_parent_thread_id)
    monkeypatch.setattr(migrate.Path, "write_text", fail_second_parent_write_and_first_restore)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    captured = capsys.readouterr()
    assert "MANUAL CLEANUP REQUIRED" in captured.err
    assert str(first_parent_index) in captured.err
    assert "MOVED" not in captured.out


def test_apply_preserves_preexisting_children_root_when_apply_fails(
    monkeypatch,
    tmp_path,
):
    migrate = load_migrate_child_sessions()
    children_root = tmp_path / ".codex" / "sessions" / "_children"
    children_root.mkdir(parents=True)
    write_session(tmp_path, "child-a", "# Child A\n")
    write_session(tmp_path, "child-b", "# Child B\n")
    original_move = migrate.shutil.move

    monkeypatch.setattr(migrate.sl, "find_jsonl_by_thread", lambda thread_id: None)
    monkeypatch.setattr(
        migrate.pl,
        "resolve_parent_thread_id",
        lambda thread_id, rollout_path=None: child_resolution("missing-parent"),
    )

    def fail_second_child_move(source, destination):
        if Path(source).name == "child-b":
            raise migrate.shutil.Error("second move failed")
        return original_move(source, destination)

    monkeypatch.setattr(migrate.shutil, "move", fail_second_child_move)

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 2

    assert children_root.is_dir()
