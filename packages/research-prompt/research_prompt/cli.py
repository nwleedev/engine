"""Command-line entry point for generating Deep Research prompt artifacts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from .composer import PromptInput, compose_prompt
from .redaction import is_denied_path, redact_text
from .scanner import (
    collect_code_blocks,
    collect_dependency_candidates,
    collect_git_context,
    collect_git_diff_candidates,
    collect_stack_trace_candidates,
    collect_symbol_candidates,
    collect_user_path_candidates,
)


def _slugify(value: str) -> str:
    """Return a conservative kebab-case topic for artifact file names."""

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "research-prompt"


def _output_dir(project_root: Path, harness: str) -> Path:
    """Return the only allowed prompt artifact directory for the harness."""

    if harness == "codex":
        return project_root / ".codex" / "deep-research-prompts"
    if harness == "claude":
        return project_root / ".claude" / "deep-research-prompts"
    raise ValueError(f"unsupported harness: {harness}")


def _unique_output_path(directory: Path, date: str, topic: str) -> Path:
    """Return a non-overwriting prompt path."""

    base = directory / f"{date}-{topic}.md"
    if not base.exists():
        return base
    for index in range(2, 1000):
        candidate = directory / f"{date}-{topic}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate prompt file name")


def build_parser() -> argparse.ArgumentParser:
    """Build the research-prompt CLI parser."""

    parser = argparse.ArgumentParser(prog="research-prompt")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--harness", choices=("codex", "claude"), required=True)
    parser.add_argument("--problem", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--log", action="append", default=[])
    parser.add_argument("--repro", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--goal", action="append", default=[])
    parser.add_argument("--expected-output", action="append", default=[])
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--max-snippet-chars", type=int, default=4000)
    parser.add_argument("--date", required=True)
    return parser


def _read_log_texts(project_root: Path, paths: list[str]) -> tuple[list[str], list[str]]:
    """Read requested log files while preserving path and secret boundaries."""

    logs: list[str] = []
    warnings: list[str] = []
    resolved_root = project_root.resolve()
    for raw_path in paths:
        if is_denied_path(raw_path):
            warnings.append(f"Denied sensitive path: {raw_path}")
            continue
        log_path = (project_root / raw_path).resolve()
        try:
            log_path.relative_to(resolved_root)
        except ValueError:
            warnings.append(f"Denied path outside project: {raw_path}")
            continue
        try:
            logs.append(redact_text(log_path.read_text(encoding="utf-8", errors="replace")))
        except OSError as error:
            warnings.append(f"Could not read {raw_path}: {error}")
    return logs, warnings


def main(argv: list[str] | None = None) -> int:
    """Generate a single Deep Research prompt Markdown artifact."""

    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    context, context_warnings = collect_git_context(project_root)
    logs, log_warnings = _read_log_texts(project_root, args.log)
    user_candidates, candidate_warnings = collect_user_path_candidates(
        project_root,
        args.path,
    )
    git_candidates, git_warnings = collect_git_diff_candidates(project_root)
    symbol_candidates, symbol_warnings = collect_symbol_candidates(project_root, args.symbol)
    dependency_candidates = collect_dependency_candidates(project_root)
    candidates = (
        user_candidates
        + collect_stack_trace_candidates(logs)
        + git_candidates
        + symbol_candidates
        + dependency_candidates
    )
    code_blocks, block_warnings = collect_code_blocks(
        project_root,
        candidates,
        max_chars=args.max_snippet_chars,
    )
    output_dir = _output_dir(project_root, args.harness)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _unique_output_path(output_dir, args.date, _slugify(args.problem))
    prompt = compose_prompt(
        PromptInput(
            problem=args.problem,
            context=[f"Project root: {project_root}", *context],
            code_blocks=code_blocks,
            logs=logs,
            reproduction=args.repro,
            constraints=args.constraint
            or ["Prefer official documentation and primary sources."],
            research_goals=args.goal
            or ["Investigate the problem using the supplied project context."],
            expected_output=args.expected_output
            or ["Source-backed findings and recommended next steps."],
            warnings=context_warnings
            + log_warnings
            + candidate_warnings
            + git_warnings
            + symbol_warnings
            + block_warnings,
        )
    )
    output_path.write_text(prompt, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
