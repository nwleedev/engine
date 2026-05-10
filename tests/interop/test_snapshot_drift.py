from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "tests" / "snapshots"


def _read_text(path: Path) -> str:
    """Read a UTF-8 text file for exact snapshot comparison."""

    return path.read_text(encoding="utf-8")


def _assert_matches_snapshot(generated: Path, snapshot: Path) -> None:
    """Assert that a generated artifact has no drift from its snapshot."""

    assert _read_text(generated) == _read_text(snapshot)


def test_codex_code_mapper_artifact_matches_snapshot() -> None:
    _assert_matches_snapshot(
        ROOT / "plugins" / "codex" / "shared-subagents" / "agents" / "code-mapper.toml",
        SNAPSHOTS / "codex" / "shared-subagents" / "code-mapper.toml",
    )


def test_claude_code_mapper_artifact_matches_snapshot() -> None:
    _assert_matches_snapshot(
        ROOT / "plugins" / "claude" / "shared-subagents" / "agents" / "code-mapper.md",
        SNAPSHOTS / "claude" / "shared-subagents" / "code-mapper.md",
    )
