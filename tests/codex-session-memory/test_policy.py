from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_policy():
    spec = importlib.util.spec_from_file_location("policy", SCRIPTS / "policy.py")
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
