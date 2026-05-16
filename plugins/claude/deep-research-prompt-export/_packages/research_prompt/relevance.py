"""Rank project files by evidence signals for prompt inclusion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SIGNAL_WEIGHTS = {
    "user_path": 100,
    "stack_trace": 80,
    "git_diff": 60,
    "symbol": 30,
    "dependency": 20,
}


@dataclass(frozen=True)
class CandidateFile:
    """A project file candidate with evidence signals for prompt inclusion."""

    path: Path
    signals: dict[str, int]
    line: int | None = None

    @property
    def score(self) -> int:
        """Return weighted relevance score."""

        return sum(
            SIGNAL_WEIGHTS.get(name, 1) * count
            for name, count in self.signals.items()
        )


def rank_candidates(candidates: list[CandidateFile]) -> list[CandidateFile]:
    """Sort candidates by relevance score and then path for deterministic output."""

    return sorted(candidates, key=lambda item: (-item.score, item.path.as_posix()))
