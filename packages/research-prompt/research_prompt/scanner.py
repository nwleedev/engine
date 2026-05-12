"""Collect prompt-ready source context from project-local evidence."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

from .redaction import is_denied_path
from .relevance import CandidateFile, rank_candidates
from .snippets import extract_excerpt


STACK_TRACE_PATH = re.compile(r'File "([^"]+)", line (\d+)')
DEFAULT_CONTEXT_LINES = 4
MAX_CANDIDATES = 20
MAX_TOTAL_SNIPPET_CHARS = 12000
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


def _resolve_inside_project(project_root: Path, path: Path) -> tuple[Path | None, str | None]:
    """Resolve a candidate path and reject project escape, including symlinks."""

    resolved_root = project_root.resolve()
    resolved_path = (project_root / path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return None, f"Denied path outside project: {path.as_posix()}"
    return resolved_path, None


def _line_range(path: Path, line: int | None, context_lines: int = DEFAULT_CONTEXT_LINES) -> str | None:
    """Return the bounded line range used for a line-window excerpt."""

    if line is None:
        return None
    try:
        total_lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return str(line)
    start = max(1, line - context_lines)
    end = min(total_lines, line + context_lines)
    return f"{start}-{end}"


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
    for raw_path in paths:
        if is_denied_path(raw_path):
            warnings.append(f"Denied sensitive path: {raw_path}")
            continue
        candidate_path, warning = _resolve_inside_project(project_root, Path(raw_path))
        if warning:
            warnings.append(warning)
            continue
        if candidate_path and candidate_path.is_file():
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


def _first_symbol_line(path: Path, symbol: str) -> int | None:
    """Find the first matching line so symbol snippets stay near the relevant code."""

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for index, line in enumerate(lines, start=1):
        if symbol in line:
            return index
    return None


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
            ["rg", "--line-number", "--no-heading", symbol],
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
                resolved, _resolve_warning = _resolve_inside_project(project_root, rel)
                if resolved is None:
                    continue
                try:
                    line = _first_symbol_line(resolved, symbol)
                    if line is not None:
                        candidates[rel] = CandidateFile(path=rel, signals={"symbol": 1}, line=line)
                except OSError:
                    continue
            continue
        for line in output.splitlines():
            raw_path, separator, raw_line = line.partition(":")
            if not separator:
                continue
            rel = Path(raw_path.strip())
            if not raw_path.strip() or is_denied_path(rel.as_posix()):
                continue
            try:
                line_number = int(raw_line.split(":", 1)[0])
            except ValueError:
                line_number = None
            candidates[rel] = CandidateFile(path=rel, signals={"symbol": 1}, line=line_number)
    return rank_candidates(list(candidates.values())), warnings


def collect_dependency_context(project_root: Path, max_items: int = 12) -> list[str]:
    """Summarize dependency versions from root manifest files without a tree walk."""

    versions: list[str] = []
    package_json = project_root / "package.json"
    if package_json.is_file():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            entries = data.get(section)
            if isinstance(entries, dict):
                versions.extend(
                    f"{name}: {version}"
                    for name, version in sorted(entries.items())
                    if isinstance(name, str) and isinstance(version, str)
                )

    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            data = {}
        project = data.get("project", {})
        dependencies = project.get("dependencies", []) if isinstance(project, dict) else []
        versions.extend(item for item in dependencies if isinstance(item, str))

    requirements = project_root / "requirements.txt"
    if requirements.is_file():
        try:
            versions.extend(
                line.strip()
                for line in requirements.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
        except OSError:
            pass

    if not versions:
        return []
    return ["Dependency versions:", *[f"- {item}" for item in versions[:max_items]]]


def collect_dependency_candidates(project_root: Path) -> list[CandidateFile]:
    """Collect dependency, workflow, Docker, and lock files as candidates."""

    candidates: list[CandidateFile] = []
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project_root)
        rel_text = rel.as_posix()
        resolved, _warning = _resolve_inside_project(project_root, rel)
        if resolved is None:
            continue
        if (
            path.name in DEPENDENCY_FILE_NAMES
            or rel_text.startswith(".github/workflows/")
            or rel_text.endswith(".lock")
        ) and not is_denied_path(rel_text):
            candidates.append(CandidateFile(path=rel, signals={"dependency": 1}))
    return rank_candidates(candidates)


def merge_candidates(candidates: list[CandidateFile]) -> list[CandidateFile]:
    """Merge duplicate path candidates so multiple signals strengthen relevance."""

    merged: dict[Path, CandidateFile] = {}
    for candidate in candidates:
        existing = merged.get(candidate.path)
        if existing is None:
            merged[candidate.path] = candidate
            continue
        signals = dict(existing.signals)
        for name, count in candidate.signals.items():
            signals[name] = signals.get(name, 0) + count
        merged[candidate.path] = CandidateFile(
            path=candidate.path,
            signals=signals,
            line=existing.line if existing.line is not None else candidate.line,
        )
    return rank_candidates(list(merged.values()))


def collect_code_blocks(
    project_root: Path,
    candidates: list[CandidateFile],
    *,
    max_chars: int = 4000,
    max_total_chars: int = MAX_TOTAL_SNIPPET_CHARS,
    max_candidates: int = MAX_CANDIDATES,
) -> tuple[list[dict[str, str]], list[str]]:
    """Read candidate file excerpts and return prompt-ready code blocks."""

    blocks: list[dict[str, str]] = []
    warnings: list[str] = []
    used_chars = 0
    for candidate in merge_candidates(candidates)[:max_candidates]:
        if is_denied_path(candidate.path.as_posix()):
            warnings.append(f"Denied sensitive path: {candidate.path.as_posix()}")
            continue
        absolute, warning = _resolve_inside_project(project_root, candidate.path)
        if warning:
            warnings.append(warning)
            continue
        if absolute is None or not absolute.is_file():
            warnings.append(f"Path not found or not a file: {candidate.path.as_posix()}")
            continue
        try:
            excerpt = extract_excerpt(
                absolute,
                line=candidate.line,
                context_lines=DEFAULT_CONTEXT_LINES,
                max_chars=max_chars,
            )
        except OSError as error:
            warnings.append(f"Could not read {candidate.path.as_posix()}: {error}")
            continue
        if blocks and used_chars + len(excerpt) > max_total_chars:
            warnings.append(f"not included due to budget: {candidate.path.as_posix()}")
            continue
        used_chars += len(excerpt)
        blocks.append(
            {
                "path": candidate.path.as_posix(),
                "reason": ", ".join(sorted(candidate.signals)),
                "line_range": _line_range(absolute, candidate.line) or "",
                "excerpt": excerpt,
            }
        )
    omitted = len(merge_candidates(candidates)) - max_candidates
    if omitted > 0:
        warnings.append(f"not included due to budget: {omitted} lower-ranked candidates")
    return blocks, warnings
