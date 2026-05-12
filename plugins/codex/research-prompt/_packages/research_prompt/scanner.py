"""Collect prompt-ready source context from user-provided project paths."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .redaction import is_denied_path
from .relevance import CandidateFile, rank_candidates
from .snippets import extract_excerpt


STACK_TRACE_PATH = re.compile(r'File "([^"]+)", line (\d+)')
DEPENDENCY_FILE_NAMES = frozenset(
    {
        "package.json",
        "pnpm-lock.yaml",
        "package-lock.json",
        "yarn.lock",
        "pyproject.toml",
        "requirements.txt",
        "Dockerfile",
    }
)


def _run_read_only(
    command: list[str],
    project_root: Path,
    timeout_seconds: int = 3,
) -> tuple[str, str | None]:
    """Run an allowed read-only command and return stdout plus optional warning."""

    try:
        result = subprocess.run(
            command,
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return "", f"{command[0]} failed: {error}"
    if result.returncode != 0:
        return result.stdout, f"{' '.join(command)} failed: exit code {result.returncode}"
    return result.stdout, None


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


def collect_git_context(project_root: Path) -> tuple[list[str], list[str]]:
    """Collect live git status and diff summary for the prompt context."""

    warnings: list[str] = []
    status, status_warning = _run_read_only(["git", "status", "--short"], project_root)
    diff, diff_warning = _run_read_only(["git", "diff", "--stat"], project_root)
    if status_warning:
        warnings.append(status_warning)
    if diff_warning:
        warnings.append(diff_warning)
    context = [f"Git status:\n{status or 'clean'}", f"Git diff stat:\n{diff or 'none'}"]
    return context, warnings


def collect_git_diff_candidates(project_root: Path) -> tuple[list[CandidateFile], list[str]]:
    """Collect changed files from git diff as relevance candidates."""

    output, warning = _run_read_only(["git", "diff", "--name-only"], project_root)
    warnings = [warning] if warning else []
    candidates = [
        CandidateFile(path=Path(line.strip()), signals={"git_diff": 1})
        for line in output.splitlines()
        if line.strip() and not is_denied_path(line.strip())
    ]
    return rank_candidates(candidates), warnings


def collect_stack_trace_candidates(log_texts: list[str]) -> list[CandidateFile]:
    """Extract file path candidates from stack traces."""

    candidates: list[CandidateFile] = []
    for text in log_texts:
        for match in STACK_TRACE_PATH.finditer(text):
            candidates.append(
                CandidateFile(
                    path=Path(match.group(1)),
                    signals={"stack_trace": 1},
                    line=int(match.group(2)),
                )
            )
    return rank_candidates(candidates)


def collect_symbol_candidates(
    project_root: Path,
    symbols: list[str],
    timeout_seconds: int = 3,
) -> tuple[list[CandidateFile], list[str]]:
    """Collect symbol match candidates using rg with Python fallback."""

    candidates: dict[Path, CandidateFile] = {}
    warnings: list[str] = []
    for symbol in symbols:
        output, warning = _run_read_only(
            ["rg", "--files-with-matches", symbol],
            project_root,
            timeout_seconds,
        )
        if warning:
            warnings.append(warning)
            for path in project_root.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(project_root)
                if is_denied_path(rel.as_posix()):
                    continue
                try:
                    if symbol in path.read_text(encoding="utf-8", errors="replace"):
                        candidates[rel] = CandidateFile(path=rel, signals={"symbol": 1})
                except OSError:
                    continue
            continue
        for line in output.splitlines():
            rel = Path(line.strip())
            if line.strip() and not is_denied_path(rel.as_posix()):
                candidates[rel] = CandidateFile(path=rel, signals={"symbol": 1})
    return rank_candidates(list(candidates.values())), warnings


def collect_dependency_candidates(project_root: Path) -> list[CandidateFile]:
    """Collect dependency, workflow, Docker, and lock files as candidates."""

    candidates: list[CandidateFile] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_root)
        rel_text = rel.as_posix()
        if (
            path.name in DEPENDENCY_FILE_NAMES
            or rel_text.startswith(".github/workflows/")
            or rel_text.endswith(".lock")
        ) and not is_denied_path(rel_text):
            candidates.append(CandidateFile(path=rel, signals={"dependency": 1}))
    return rank_candidates(candidates)


def collect_code_blocks(
    project_root: Path,
    candidates: list[CandidateFile],
    *,
    max_chars: int = 4000,
) -> tuple[list[dict[str, str]], list[str]]:
    """Read candidate file excerpts and return prompt-ready code blocks."""

    blocks: list[dict[str, str]] = []
    warnings: list[str] = []
    for candidate in candidates:
        absolute = project_root / candidate.path
        try:
            excerpt = extract_excerpt(absolute, line=candidate.line, max_chars=max_chars)
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
