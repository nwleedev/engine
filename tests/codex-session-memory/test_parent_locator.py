import importlib.util
import json
import sqlite3
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"
PARENT_LOCATOR = SCRIPTS / "parent_locator.py"


def load_parent_locator():
    spec = importlib.util.spec_from_file_location("parent_locator", PARENT_LOCATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_state_db(path: Path, *, edges: bool = True, threads: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    if edges:
        conn.execute(
            "CREATE TABLE thread_spawn_edges ("
            "parent_thread_id TEXT NOT NULL, "
            "child_thread_id TEXT NOT NULL PRIMARY KEY, "
            "status TEXT NOT NULL)"
        )
    if threads:
        conn.execute(
            "CREATE TABLE threads ("
            "id TEXT PRIMARY KEY, "
            "rollout_path TEXT NOT NULL, "
            "source TEXT NOT NULL)"
        )
    conn.commit()
    conn.close()


def test_reads_parent_from_session_meta_after_noise_event(tmp_path):
    locator = load_parent_locator()
    jsonl = tmp_path / "rollout-child.jsonl"
    jsonl.write_text(
        json.dumps({"type": "noise", "payload": {}}) + "\n"
        + json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "source": {
                        "subagent": {
                            "thread_spawn": {
                                "parent_thread_id": "parent-123",
                            },
                        },
                    },
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = locator.resolve_parent_thread_id(
        thread_id="child-123",
        rollout_path=jsonl,
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-123"
    assert result.source == "rollout_session_meta"
    assert result.confidence == "high"
    assert result.warnings == ()


def test_rollout_child_evidence_without_parent_stops_before_state_db(tmp_path):
    locator = load_parent_locator()
    jsonl = tmp_path / "rollout-child.jsonl"
    jsonl.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "source": {
                        "subagent": {
                            "thread_spawn": {},
                        },
                    },
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-from-db", "child-no-rollout-parent", "open"),
    )
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-no-rollout-parent",
        rollout_path=jsonl,
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "child"
    assert result.parent_thread_id is None
    assert result.source == "rollout_session_meta"
    assert result.confidence == "medium"


def test_rollout_scan_stops_after_50_lines(tmp_path):
    locator = load_parent_locator()
    jsonl = tmp_path / "rollout-child.jsonl"
    noise_lines = [json.dumps({"type": "noise", "payload": {"index": index}}) for index in range(50)]
    late_session_meta = json.dumps(
        {
            "type": "session_meta",
            "payload": {
                "source": {
                    "subagent": {
                        "thread_spawn": {
                            "parent_thread_id": "parent-on-line-51",
                        },
                    },
                },
            },
        }
    )
    jsonl.write_text("\n".join(noise_lines + [late_session_meta]) + "\n", encoding="utf-8")

    result = locator.resolve_parent_thread_id(
        "child-line-51",
        rollout_path=jsonl,
        codex_home=tmp_path / ".codex",
        sqlite_home=tmp_path / "sqlite-home",
    )

    assert result.role == "main"
    assert result.parent_thread_id is None
    assert result.source == "none"
    assert result.confidence == "none"


def test_reads_parent_from_thread_spawn_edges(tmp_path):
    locator = load_parent_locator()
    db = tmp_path / "sqlite-home" / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-456", "child-456", "open"),
    )
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-456",
        sqlite_home=tmp_path / "sqlite-home",
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-456"
    assert result.source == "state_db_thread_spawn_edges"
    assert result.confidence == "high"


def test_reads_parent_from_threads_source(tmp_path):
    locator = load_parent_locator()
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?)",
        (
            "child-789",
            "rollout-child-789.jsonl",
            json.dumps(
                {
                    "subagent": {
                        "thread_spawn": {
                            "parent_thread_id": "parent-789",
                            "depth": 1,
                        },
                    },
                }
            ),
        ),
    )
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-789",
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-789"
    assert result.source == "state_db_threads_source"
    assert result.confidence == "medium"


def test_missing_state_schema_returns_miss(tmp_path):
    locator = load_parent_locator()
    db = tmp_path / ".codex" / "state_5.sqlite"
    db.parent.mkdir(parents=True)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE unrelated (id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-missing",
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "main"
    assert result.parent_thread_id is None
    assert result.source == "none"
    assert result.confidence == "none"


def test_falls_back_to_newer_state_db_when_state_5_misses(tmp_path):
    locator = load_parent_locator()
    sqlite_home = tmp_path / "sqlite-home"
    state_5 = sqlite_home / "state_5.sqlite"
    state_6 = sqlite_home / "state_6.sqlite"
    make_state_db(state_5)
    make_state_db(state_6)
    conn = sqlite3.connect(state_6)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-state-6", "child-state-6", "open"),
    )
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-state-6",
        sqlite_home=sqlite_home,
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-state-6"
    assert result.source == "state_db_thread_spawn_edges"


def test_broken_state_db_candidate_does_not_raise(tmp_path):
    locator = load_parent_locator()
    sqlite_home = tmp_path / "sqlite-home"
    sqlite_home.mkdir()
    (sqlite_home / "state_broken.sqlite").symlink_to(sqlite_home / "missing.sqlite")

    result = locator.resolve_parent_thread_id(
        "child-broken-candidate",
        sqlite_home=sqlite_home,
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "main"
    assert result.parent_thread_id is None
    assert result.source == "none"


def test_malformed_threads_source_warns_and_returns_miss(tmp_path):
    locator = load_parent_locator()
    db = tmp_path / ".codex" / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO threads VALUES (?, ?, ?)",
        ("child-bad-source", "rollout-child-bad-source.jsonl", "{not-json"),
    )
    conn.commit()
    conn.close()

    result = locator.resolve_parent_thread_id(
        "child-bad-source",
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "main"
    assert result.parent_thread_id is None
    assert result.source == "none"
    assert result.confidence == "none"
    assert result.warnings == ("malformed threads.source json",)


def test_malformed_rollout_json_warns_and_returns_miss(tmp_path):
    locator = load_parent_locator()
    jsonl = tmp_path / "rollout-child.jsonl"
    jsonl.write_text(
        '{"type":"session_meta","payload":\n'
        + json.dumps({"type": "noise", "payload": {}})
        + "\n",
        encoding="utf-8",
    )

    result = locator.resolve_parent_thread_id(
        "child-malformed",
        rollout_path=jsonl,
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "main"
    assert result.parent_thread_id is None
    assert result.source == "none"
    assert result.confidence == "none"
    assert result.warnings == ("malformed rollout json line 1",)
