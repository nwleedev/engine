import importlib.util
import sys
from pathlib import Path


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


def child_index(session_id: str, parent_id: str, body: str = "# Child\n") -> str:
    return (
        "---\n"
        f"thread_id: {session_id}\n"
        "role: child\n"
        f"parent_session_id: {parent_id}\n"
        "summary: keep me\n"
        "---\n\n"
        f"{body}"
    )


def test_migration_does_not_load_internal_parent_or_graph_modules(monkeypatch):
    loaded = []
    original_spec_from_file_location = importlib.util.spec_from_file_location

    def fake_spec_from_file_location(module_name, module_path):
        loaded.append(Path(module_path).name)
        return original_spec_from_file_location(module_name, module_path)

    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)
    migrate = load_migrate_child_sessions()

    assert migrate is not None
    assert "parent_locator.py" not in loaded
    assert "graph_store.py" not in loaded
    assert "jsonl_parser.py" not in loaded


def test_dry_run_uses_filesystem_and_frontmatter_only(tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    main_dir = write_session(tmp_path, "main-thread")
    child_dir = write_session(
        tmp_path,
        "top-level-child",
        child_index("top-level-child", "parent-thread"),
    )
    legacy_child_dir = write_legacy_child_session(
        tmp_path,
        "children-child",
        child_index("children-child", "parent-thread"),
    )
    write_session(tmp_path, "_children")
    write_session(tmp_path, ".hidden")

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


def test_apply_moves_legacy_sessions_and_strips_relationship_frontmatter(tmp_path):
    migrate = load_migrate_child_sessions()
    child_dir = write_session(
        tmp_path,
        "child-thread",
        child_index("child-thread", "parent-thread", body="# Child\n\nBody stays.\n"),
    )
    parent_dir = write_session(tmp_path, "parent-thread", "# Parent\n")
    original_parent_index = (parent_dir / "INDEX.md").read_text(encoding="utf-8")

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    text = (destination / "INDEX.md").read_text(encoding="utf-8")
    assert "role:" not in text
    assert "parent_session_id:" not in text
    assert "summary: keep me" in text
    assert "Body stays." in text
    assert not parent_dir.exists()
    assert (
        flat_destination(tmp_path, "parent-thread") / "INDEX.md"
    ).read_text(encoding="utf-8") == original_parent_index


def test_apply_moves_legacy_children_child_to_flat_destination(tmp_path):
    migrate = load_migrate_child_sessions()
    child_dir = write_legacy_child_session(tmp_path, "child-thread", "# Legacy Child\n")

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    destination = flat_destination(tmp_path, "child-thread")
    assert not child_dir.exists()
    assert destination.is_dir()
    assert (destination / "INDEX.md").read_text(encoding="utf-8") == "# Legacy Child\n"


def test_apply_cleans_synthetic_parent_child_links_from_frontmatter_parent(tmp_path):
    migrate = load_migrate_child_sessions()
    write_session(
        tmp_path,
        "parent-thread",
        "# Parent\n\n- [child-thread](../_children/child-thread/INDEX.md) - migrated child session\n",
    )
    write_legacy_child_session(
        tmp_path,
        "child-thread",
        child_index("child-thread", "parent-thread"),
    )

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == 0

    parent_index = flat_destination(tmp_path, "parent-thread") / "INDEX.md"
    assert "migrated child session" not in parent_index.read_text(encoding="utf-8")


def test_apply_preflights_destination_conflicts(tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    write_session(tmp_path, "child-thread")
    destination = flat_destination(tmp_path, "child-thread")
    destination.mkdir(parents=True)
    (destination / "INDEX.md").write_text("# Existing\n", encoding="utf-8")

    assert migrate.main(["--root", str(tmp_path), "--apply"]) == migrate.EXIT_OPERATION_FAILED

    assert "destination exists" in capsys.readouterr().err


def test_root_errors_return_exit_2(tmp_path, capsys):
    migrate = load_migrate_child_sessions()
    missing_root = tmp_path / "missing"

    assert migrate.main(["--root", str(missing_root)]) == 2

    assert "root does not exist" in capsys.readouterr().err
