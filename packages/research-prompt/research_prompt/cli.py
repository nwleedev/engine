"""Command-line entry point for generating Deep Research prompt artifacts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from .composer import PromptInput, compose_prompt
from .scanner import collect_code_blocks, collect_user_path_candidates


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
    parser.add_argument("--date", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate a single Deep Research prompt Markdown artifact."""

    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root).resolve()
    candidates, candidate_warnings = collect_user_path_candidates(
        project_root,
        args.path,
    )
    code_blocks, block_warnings = collect_code_blocks(project_root, candidates)
    output_dir = _output_dir(project_root, args.harness)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _unique_output_path(output_dir, args.date, _slugify(args.problem))
    prompt = compose_prompt(
        PromptInput(
            problem=args.problem,
            context=[f"Project root: {project_root}"],
            code_blocks=code_blocks,
            logs=[],
            reproduction=[],
            constraints=["Prefer official documentation and primary sources."],
            research_goals=["Investigate the problem using the supplied project context."],
            expected_output=["Source-backed findings and recommended next steps."],
            warnings=candidate_warnings + block_warnings,
        )
    )
    output_path.write_text(prompt, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
