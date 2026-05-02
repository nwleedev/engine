"""Save policy for codex-session-memory automatic checkpoints."""
from dataclasses import dataclass
from datetime import datetime, timezone


MIN_DELTA_CHARS = 4000
MIN_TIME_GAP_SECONDS = 300
TOOL_OUTPUT_CHARS_THRESHOLD = 20000
HARD_CAP_DELTA_CHARS = 60000


@dataclass(frozen=True)
class SaveDecision:
    save: bool
    reason: str


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def should_save(
    *,
    delta_chars: int,
    tool_output_chars: int,
    last_saved_at: datetime | None,
    now: datetime,
    force: bool = False,
) -> SaveDecision:
    if force:
        return SaveDecision(True, "force")
    if delta_chars >= HARD_CAP_DELTA_CHARS:
        return SaveDecision(True, "hard-cap")
    if tool_output_chars >= TOOL_OUTPUT_CHARS_THRESHOLD:
        return SaveDecision(True, "tool-output-threshold")
    if delta_chars < MIN_DELTA_CHARS:
        return SaveDecision(False, "below-threshold")
    if last_saved_at is None:
        return SaveDecision(True, "first-save")
    elapsed = (_as_utc(now) - _as_utc(last_saved_at)).total_seconds()
    if elapsed >= MIN_TIME_GAP_SECONDS:
        return SaveDecision(True, "time-gap")
    return SaveDecision(False, "within-time-gap")
