"""Collect prompt-ready source context from user-provided project paths."""

from __future__ import annotations

from pathlib import Path

from .redaction import is_denied_path
from .relevance import CandidateFile, rank_candidates
from .snippets import extract_excerpt


def collect_user_path_candidates(
    project_root: Path,
    paths: list[str],
) -> tuple[list[CandidateFile], list[str]]:
    """Collect user-mentioned path candidates without reading denied paths."""

    candidates: list[CandidateFile] = []
    warnings: list[str] = []
    resolved_root = project_root.resolve()
    for raw_path in paths:
        if is_denied_path(raw_path):
            warnings.append(f"Denied sensitive path: {raw_path}")
            continue
        candidate_path = (project_root / raw_path).resolve()
        try:
            candidate_path.relative_to(resolved_root)
        except ValueError:
            warnings.append(f"Denied path outside project: {raw_path}")
            continue
        if candidate_path.is_file():
            candidates.append(CandidateFile(path=Path(raw_path), signals={"user_path": 1}))
        else:
            warnings.append(f"Path not found or not a file: {raw_path}")
    return rank_candidates(candidates), warnings


def collect_code_blocks(
    project_root: Path,
    candidates: list[CandidateFile],
) -> tuple[list[dict[str, str]], list[str]]:
    """Read candidate file excerpts and return prompt-ready code blocks."""

    blocks: list[dict[str, str]] = []
    warnings: list[str] = []
    for candidate in candidates:
        absolute = project_root / candidate.path
        try:
            excerpt = extract_excerpt(absolute)
        except OSError as error:
            warnings.append(f"Could not read {candidate.path.as_posix()}: {error}")
            continue
        blocks.append(
            {
                "path": candidate.path.as_posix(),
                "reason": ", ".join(sorted(candidate.signals)),
                "excerpt": excerpt,
            }
        )
    return blocks, warnings
