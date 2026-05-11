import importlib.util
import os
import sqlite3
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"
GRAPH_STORE = SCRIPTS / "graph_store.py"


def load_graph_store():
    spec = importlib.util.spec_from_file_location("graph_store", GRAPH_STORE)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_state_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE thread_spawn_edges ("
        "parent_thread_id TEXT NOT NULL, "
        "child_thread_id TEXT NOT NULL PRIMARY KEY, "
        "status TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def make_empty_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE unrelated (id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()


def insert_edge(path: Path, parent: str, child: str, status: str = "open"):
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO thread_spawn_edges VALUES (?, ?, ?)", (parent, child, status))
    conn.commit()
    conn.close()


def test_parent_children_and_role_from_state_db(tmp_path):
    graph_store = load_graph_store()
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent", "child-b", "closed")
    insert_edge(db, "parent", "child-a", "open")

    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.parent_of("child-a").parent_thread_id == "parent"
    assert store.children_of("parent") == ["child-a", "child-b"]
    assert store.children_of("parent", status="open") == ["child-a"]
    assert store.role_of("child-a").role == "child"
    assert store.role_of("parent").role == "main"


def test_descendants_are_breadth_first_and_stable(tmp_path):
    graph_store = load_graph_store()
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "root", "b")
    insert_edge(db, "root", "a")
    insert_edge(db, "a", "z")
    insert_edge(db, "b", "c")

    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.descendants_of("root") == ["a", "b", "c", "z"]


def test_missing_graph_is_unavailable_without_raising(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    monkeypatch.setattr(graph_store.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.parent_of("child").available is False
    assert store.children_of("parent") == []
    assert store.descendants_of("parent") == []
    assert store.role_of("thread").role == "main"


def test_missing_schema_is_unavailable_without_raising(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    monkeypatch.setattr(graph_store.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_empty_db(db)

    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.parent_of("child").available is False
    assert store.children_of("parent") == []
    assert store.descendants_of("parent") == []
    assert store.role_of("thread").role == "main"


def test_reads_from_explicit_sqlite_home(tmp_path):
    graph_store = load_graph_store()
    db = tmp_path / "sqlite-home" / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-from-sqlite-home", "child")

    store = graph_store.GraphStore(
        codex_home=tmp_path / ".codex",
        sqlite_home=tmp_path / "sqlite-home",
    )

    assert store.parent_of("child").parent_thread_id == "parent-from-sqlite-home"


def test_reads_from_codex_sqlite_home_env(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    sqlite_home = tmp_path / "env-sqlite"
    db = sqlite_home / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-from-env", "child")
    monkeypatch.setenv("CODEX_SQLITE_HOME", str(sqlite_home))

    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.parent_of("child").parent_thread_id == "parent-from-env"


def test_reads_from_configured_sqlite_home(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    codex_home = tmp_path / ".codex"
    sqlite_home = tmp_path / "configured-sqlite"
    codex_home.mkdir(parents=True)
    codex_home.joinpath("config.toml").write_text(
        'sqlite_home = "../configured-sqlite"\n',
        encoding="utf-8",
    )
    db = sqlite_home / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-from-config", "child")

    store = graph_store.GraphStore(codex_home=codex_home)

    assert store.parent_of("child").parent_thread_id == "parent-from-config"


def test_reads_from_codex_home_candidate(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-from-codex-home", "child")

    store = graph_store.GraphStore(codex_home=tmp_path / ".codex")

    assert store.parent_of("child").parent_thread_id == "parent-from-codex-home"


def test_default_home_fallback_is_included_after_codex_home(monkeypatch, tmp_path):
    graph_store = load_graph_store()
    monkeypatch.delenv("CODEX_SQLITE_HOME", raising=False)
    fake_home = tmp_path / "home"
    default_codex_home = fake_home / ".codex"
    db = default_codex_home / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-from-default-home", "child")
    monkeypatch.setattr(graph_store.Path, "home", classmethod(lambda cls: fake_home))

    store = graph_store.GraphStore(codex_home=tmp_path / "empty-codex-home")

    assert store.parent_of("child").parent_thread_id == "parent-from-default-home"


def test_state_5_is_preferred_over_newer_state_db(tmp_path):
    graph_store = load_graph_store()
    sqlite_home = tmp_path / "sqlite-home"
    state_5 = sqlite_home / "state_5.sqlite"
    newer_state = sqlite_home / "state_9.sqlite"
    make_state_db(state_5)
    make_state_db(newer_state)
    insert_edge(state_5, "parent-from-state-5", "child")
    insert_edge(newer_state, "parent-from-newer", "child")
    os.utime(state_5, (1, 1))
    os.utime(newer_state, (2, 2))

    store = graph_store.GraphStore(sqlite_home=sqlite_home)

    assert store.parent_of("child").parent_thread_id == "parent-from-state-5"


def test_falls_back_to_newer_state_db_when_state_5_misses(tmp_path):
    graph_store = load_graph_store()
    sqlite_home = tmp_path / "sqlite-home"
    state_5 = sqlite_home / "state_5.sqlite"
    state_6 = sqlite_home / "state_6.sqlite"
    make_state_db(state_5)
    make_state_db(state_6)
    insert_edge(state_6, "parent-state-6", "child-state-6")
    os.utime(state_5, (1, 1))
    os.utime(state_6, (2, 2))

    store = graph_store.GraphStore(sqlite_home=sqlite_home)

    assert store.parent_of("child-state-6").parent_thread_id == "parent-state-6"
    assert store.children_of("parent-state-6") == ["child-state-6"]


def test_broken_candidate_does_not_block_next_valid_state_db(tmp_path):
    graph_store = load_graph_store()
    sqlite_home = tmp_path / "sqlite-home"
    sqlite_home.mkdir()
    broken = sqlite_home / "state_5.sqlite"
    broken.write_text("not sqlite", encoding="utf-8")
    valid = sqlite_home / "state_6.sqlite"
    make_state_db(valid)
    insert_edge(valid, "parent-after-broken", "child-after-broken")
    os.utime(broken, (3, 3))
    os.utime(valid, (2, 2))

    store = graph_store.GraphStore(sqlite_home=sqlite_home)

    assert store.parent_of("child-after-broken").parent_thread_id == "parent-after-broken"
    assert store.children_of("parent-after-broken") == ["child-after-broken"]


def test_state_dbs_without_state_5_use_newest_mtime_first(tmp_path):
    graph_store = load_graph_store()
    sqlite_home = tmp_path / "sqlite-home"
    older_state = sqlite_home / "state_3.sqlite"
    newer_state = sqlite_home / "state_4.sqlite"
    make_state_db(older_state)
    make_state_db(newer_state)
    insert_edge(older_state, "parent-from-older", "child")
    insert_edge(newer_state, "parent-from-newer", "child")
    os.utime(older_state, (1, 1))
    os.utime(newer_state, (2, 2))

    store = graph_store.GraphStore(sqlite_home=sqlite_home)

    assert store.parent_of("child").parent_thread_id == "parent-from-newer"
