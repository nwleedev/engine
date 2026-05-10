"""Narration policy gate: should_narrate(event, delta, index_data)."""
from datetime import datetime, timezone

NARRATION_MIN_DELTA = 1_000
NARRATION_HARD_CAP = 60_000
NARRATION_TIME_GAP = 300

LIFECYCLE_EVENTS = {"SessionEnd", "ManualCheckpoint"}


def format_messages(messages: list) -> str:
    return "\n".join(f"[{m['role']}] {m['text']}" for m in messages)


def _elapsed_seconds(last_written: str) -> float:
    if not last_written:
        return float("inf")
    try:
        last = datetime.fromisoformat(last_written)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - last).total_seconds()
    except Exception:
        return float("inf")


def should_narrate(event: str, delta: list, index_data: dict) -> bool:
    if event in LIFECYCLE_EVENTS:
        return bool(delta)
    if not delta:
        return False
    text_len = len(format_messages(delta))
    if text_len < NARRATION_MIN_DELTA:
        return False
    if text_len >= NARRATION_HARD_CAP:
        return True
    return _elapsed_seconds(index_data.get("last_context_written_at", "")) >= NARRATION_TIME_GAP
