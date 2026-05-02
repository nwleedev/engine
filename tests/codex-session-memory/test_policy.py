import json
import os
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_policy():
    spec = importlib.util.spec_from_file_location("policy", SCRIPTS / "policy.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_lockfile():
    spec = importlib.util.spec_from_file_location("lockfile", SCRIPTS / "lockfile.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_force_always_saves():
    policy = load_policy()
    decision = policy.should_save(
        delta_chars=0,
        tool_output_chars=0,
        last_saved_at=datetime.now(timezone.utc),
        now=datetime.now(timezone.utc),
        force=True,
    )
    assert decision.save is True
    assert decision.reason == "force"


def test_small_recent_delta_skips():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=200,
        tool_output_chars=0,
        last_saved_at=now - timedelta(seconds=30),
        now=now,
        force=False,
    )
    assert decision.save is False
    assert decision.reason == "below-threshold"


def test_mcp_heavy_delta_saves_before_time_gap():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=500,
        tool_output_chars=25000,
        last_saved_at=now - timedelta(seconds=30),
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "tool-output-threshold"


def test_hard_cap_delta_saves():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=policy.HARD_CAP_DELTA_CHARS,
        tool_output_chars=0,
        last_saved_at=now,
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "hard-cap"


def test_first_save_after_minimum_delta_saves():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=policy.MIN_DELTA_CHARS,
        tool_output_chars=0,
        last_saved_at=None,
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "first-save"


def test_elapsed_time_gap_saves():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=policy.MIN_DELTA_CHARS,
        tool_output_chars=0,
        last_saved_at=now - timedelta(seconds=policy.MIN_TIME_GAP_SECONDS),
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "time-gap"


def test_minimum_delta_threshold_equality_within_gap_skips():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=policy.MIN_DELTA_CHARS,
        tool_output_chars=0,
        last_saved_at=now - timedelta(seconds=policy.MIN_TIME_GAP_SECONDS - 1),
        now=now,
        force=False,
    )
    assert decision.save is False
    assert decision.reason == "within-time-gap"


def test_tool_output_threshold_equality_saves():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    decision = policy.should_save(
        delta_chars=0,
        tool_output_chars=policy.TOOL_OUTPUT_CHARS_THRESHOLD,
        last_saved_at=now,
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "tool-output-threshold"


def test_naive_last_saved_at_is_normalized_to_utc():
    policy = load_policy()
    now = datetime.now(timezone.utc)
    naive_last_saved_at = (now - timedelta(seconds=policy.MIN_TIME_GAP_SECONDS)).replace(tzinfo=None)
    decision = policy.should_save(
        delta_chars=policy.MIN_DELTA_CHARS,
        tool_output_chars=0,
        last_saved_at=naive_last_saved_at,
        now=now,
        force=False,
    )
    assert decision.save is True
    assert decision.reason == "time-gap"


def test_lock_creates_metadata_and_deletes_after_context(tmp_path):
    lockfile = load_lockfile()
    path = tmp_path / "session.lock"

    with lockfile.acquire_lock(path):
        assert path.exists()
        metadata = json.loads(path.read_text(encoding="utf-8"))
        assert metadata["pid"] == os.getpid()
        assert datetime.fromisoformat(metadata["created_at"]).tzinfo is not None

    assert not path.exists()


def test_lock_deletes_after_context_exception(tmp_path):
    lockfile = load_lockfile()
    path = tmp_path / "session.lock"

    with pytest.raises(RuntimeError, match="body failed"):
        with lockfile.acquire_lock(path):
            assert path.exists()
            raise RuntimeError("body failed")

    assert not path.exists()


def test_existing_lock_times_out(tmp_path):
    lockfile = load_lockfile()
    path = tmp_path / "session.lock"
    path.write_text("existing", encoding="utf-8")

    with pytest.raises(TimeoutError, match="lock timeout"):
        with lockfile.acquire_lock(path, timeout_seconds=0.01):
            pass


def test_lock_recovers_dead_process_lock(tmp_path):
    lockfile = load_lockfile()
    path = tmp_path / "session.lock"
    path.write_text('{"pid": 999999999, "created_at": "2099-01-02T00:00:00+00:00"}\n')

    with lockfile.acquire_lock(path, timeout_seconds=0.01):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        assert metadata["pid"] == os.getpid()


def test_lock_does_not_remove_replaced_active_lock(monkeypatch, tmp_path):
    lockfile = load_lockfile()
    path = tmp_path / "session.lock"
    path.write_text('{"pid": 999999999, "created_at": "2099-01-02T00:00:00+00:00"}\n')

    def replace_lock(lock_path):
        lock_path.unlink()
        lock_path.write_text(json.dumps({"pid": os.getpid(), "created_at": "2099-01-02T00:00:01+00:00"}))
        return True

    monkeypatch.setattr(lockfile, "_lock_process_is_dead", replace_lock)

    with pytest.raises(TimeoutError, match="lock timeout"):
        with lockfile.acquire_lock(path, timeout_seconds=0.01):
            pass
