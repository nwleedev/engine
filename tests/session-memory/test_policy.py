from datetime import datetime, timezone, timedelta
import policy as pol


def _ts(seconds_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)).replace(tzinfo=None).isoformat(timespec="seconds")


def _msg(text: str) -> dict:
    return {"role": "user", "text": text, "uuid": "u"}


def test_lifecycle_event_narrates_when_delta_present():
    delta = [_msg("hi")]
    assert pol.should_narrate("SessionEnd", delta, {}) is True
    assert pol.should_narrate("ManualCheckpoint", delta, {}) is True


def test_lifecycle_event_skips_when_no_delta():
    assert pol.should_narrate("SessionEnd", [], {}) is False


def test_skips_when_delta_below_min_floor():
    delta = [_msg("ok")]
    idx = {"last_context_written_at": _ts(1000)}
    assert pol.should_narrate("Stop", delta, idx) is False


def test_narrates_when_hard_cap_reached():
    big = "x" * 70_000
    delta = [_msg(big)]
    idx = {"last_context_written_at": _ts(10)}
    assert pol.should_narrate("Stop", delta, idx) is True


def test_narrates_when_time_gap_elapsed():
    delta = [_msg("a" * 5_000)]
    idx = {"last_context_written_at": _ts(400)}
    assert pol.should_narrate("Stop", delta, idx) is True


def test_skips_when_time_gap_not_elapsed():
    delta = [_msg("a" * 5_000)]
    idx = {"last_context_written_at": _ts(60)}
    assert pol.should_narrate("Stop", delta, idx) is False


def test_first_narration_when_no_last_write():
    delta = [_msg("a" * 5_000)]
    idx = {"last_context_written_at": ""}
    assert pol.should_narrate("Stop", delta, idx) is True


def test_constants_match_spec():
    assert pol.NARRATION_MIN_DELTA == 1_000
    assert pol.NARRATION_HARD_CAP == 60_000
    assert pol.NARRATION_TIME_GAP == 300
