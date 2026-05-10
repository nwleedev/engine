import importlib.util
import json
import sqlite3
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory" / "scripts"
PARENT_LOCATOR = SCRIPTS / "parent_locator.py"


def load_parent_locator():
    spec = importlib.util.spec_from_file_location("parent_locator", PARENT_LOCATOR)
    assert spec is not None
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


def insert_edge(db: Path, parent_thread_id: str, child_thread_id: str) -> None:
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        (parent_thread_id, child_thread_id, "open"),
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


def test_rollout_child_evidence_without_parent_falls_back_to_state_db(tmp_path):
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
    assert result.parent_thread_id == "parent-from-db"
    assert result.source == "state_db_thread_spawn_edges"
    assert result.confidence == "high"


def test_rollout_child_evidence_without_parent_fails_closed_after_state_db_miss(tmp_path):
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

    result = locator.resolve_parent_thread_id(
        "child-no-parent-anywhere",
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


def test_reads_state_db_from_codex_sqlite_home_env(monkeypatch, tmp_path):
    locator = load_parent_locator()
    sqlite_home = tmp_path / "custom-sqlite"
    db = sqlite_home / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-env-sqlite", "child-env-sqlite", "open"),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("CODEX_SQLITE_HOME", str(sqlite_home))

    result = locator.resolve_parent_thread_id(
        "child-env-sqlite",
        codex_home=tmp_path / ".codex",
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-env-sqlite"
    assert result.source == "state_db_thread_spawn_edges"


def test_expands_explicit_sqlite_home(monkeypatch, tmp_path):
    locator = load_parent_locator()
    user_home = tmp_path / "user-home"
    sqlite_home = user_home / "explicit-sqlite"
    db = sqlite_home / "state_5.sqlite"
    make_state_db(db)
    insert_edge(db, "parent-explicit-tilde", "child-explicit-tilde")
    monkeypatch.setenv("HOME", str(user_home))

    result = locator.resolve_parent_thread_id(
        "child-explicit-tilde",
        sqlite_home="~/explicit-sqlite",
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-explicit-tilde"
    assert result.source == "state_db_thread_spawn_edges"


def test_reads_state_db_from_codex_config_sqlite_home(tmp_path):
    locator = load_parent_locator()
    codex_home = tmp_path / ".codex"
    sqlite_home = tmp_path / "configured-sqlite"
    db = sqlite_home / "state_5.sqlite"
    make_state_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        ("parent-config-sqlite", "child-config-sqlite", "open"),
    )
    conn.commit()
    conn.close()
    codex_home.mkdir()
    (codex_home / "config.toml").write_text(
        f'sqlite_home = "{sqlite_home}"\n',
        encoding="utf-8",
    )

    result = locator.resolve_parent_thread_id(
        "child-config-sqlite",
        codex_home=codex_home,
    )

    assert result.role == "child"
    assert result.parent_thread_id == "parent-config-sqlite"
    assert result.source == "state_db_thread_spawn_edges"


def test_state_db_candidate_home_precedence(monkeypatch, tmp_path):
    locator = load_parent_locator()
    child_id = "child-precedence"
    explicit_home = tmp_path / "explicit-sqlite"
    env_home = tmp_path / "env-sqlite"
    config_home = tmp_path / "config-sqlite"
    project_home = tmp_path / ".codex"
    user_home = tmp_path / "user-home"
    user_codex_home = user_home / ".codex"

    candidates = [
        (explicit_home, "parent-explicit"),
        (env_home, "parent-env"),
        (config_home, "parent-config"),
        (project_home, "parent-project"),
        (user_codex_home, "parent-user"),
    ]
    for home, parent_id in candidates:
        db = home / "state_5.sqlite"
        make_state_db(db)
        insert_edge(db, parent_id, child_id)

    project_home.mkdir(exist_ok=True)
    (project_home / "config.toml").write_text(
        f'sqlite_home = "{config_home}"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_SQLITE_HOME", str(env_home))
    monkeypatch.setenv("HOME", str(user_home))

    explicit_result = locator.resolve_parent_thread_id(
        child_id,
        codex_home=project_home,
        sqlite_home=explicit_home,
    )
    env_result = locator.resolve_parent_thread_id(
        child_id,
        codex_home=project_home,
    )
    monkeypatch.delenv("CODEX_SQLITE_HOME")
    config_result = locator.resolve_parent_thread_id(
        child_id,
        codex_home=project_home,
    )
    (project_home / "config.toml").unlink()
    project_result = locator.resolve_parent_thread_id(
        child_id,
        codex_home=project_home,
    )
    project_state = project_home / "state_5.sqlite"
    project_state.unlink()
    user_result = locator.resolve_parent_thread_id(
        child_id,
        codex_home=project_home,
    )

    assert explicit_result.parent_thread_id == "parent-explicit"
    assert env_result.parent_thread_id == "parent-env"
    assert config_result.parent_thread_id == "parent-config"
    assert project_result.parent_thread_id == "parent-project"
    assert user_result.parent_thread_id == "parent-user"


def test_state_db_candidate_home_fallback_after_miss(monkeypatch, tmp_path):
    locator = load_parent_locator()
    explicit_home = tmp_path / "explicit-sqlite"
    env_home = tmp_path / "env-sqlite"
    config_home = tmp_path / "config-sqlite"
    project_home = tmp_path / ".codex"
    user_home = tmp_path / "user-home"
    user_codex_home = user_home / ".codex"

    homes = [explicit_home, env_home, config_home, project_home, user_codex_home]
    for index, home in enumerate(homes):
        db = home / "state_5.sqlite"
        make_state_db(db)
        insert_edge(db, f"parent-noise-{index}", f"child-noise-{index}")

    insert_edge(env_home / "state_5.sqlite", "parent-env-hit", "child-env-hit")
    insert_edge(config_home / "state_5.sqlite", "parent-config-hit", "child-config-hit")
    insert_edge(project_home / "state_5.sqlite", "parent-project-hit", "child-project-hit")
    insert_edge(user_codex_home / "state_5.sqlite", "parent-user-hit", "child-user-hit")

    (project_home / "config.toml").write_text(
        f'sqlite_home = "{config_home}"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_SQLITE_HOME", str(env_home))
    monkeypatch.setenv("HOME", str(user_home))

    env_result = locator.resolve_parent_thread_id(
        "child-env-hit",
        codex_home=project_home,
        sqlite_home=explicit_home,
    )
    config_result = locator.resolve_parent_thread_id(
        "child-config-hit",
        codex_home=project_home,
        sqlite_home=explicit_home,
    )
    project_result = locator.resolve_parent_thread_id(
        "child-project-hit",
        codex_home=project_home,
        sqlite_home=explicit_home,
    )
    user_result = locator.resolve_parent_thread_id(
        "child-user-hit",
        codex_home=project_home,
        sqlite_home=explicit_home,
    )

    assert env_result.parent_thread_id == "parent-env-hit"
    assert config_result.parent_thread_id == "parent-config-hit"
    assert project_result.parent_thread_id == "parent-project-hit"
    assert user_result.parent_thread_id == "parent-user-hit"


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
