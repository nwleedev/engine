from __future__ import annotations

from pathlib import Path


FORBIDDEN_LEGACY_NAMES = (
    "requirements-clarifier",
    "research-crosscheck",
    "task-planner",
    "review-checklist",
    "verification-evidence",
    "online-researcher",
    "spec-reviewer",
)

REQUIRED_SHARED_SKILL_REFERENCES = (
    "workflow-artifacts.md",
    "deep-research-pipeline.md",
    "downstream-test-contracts.md",
)

REQUIRED_SHARED_SUBAGENTS = (
    "test-adequacy-reviewer",
    "closure-reviewer",
)

SHARED_SKILL_ROOTS = (
    ("codex", Path("plugins/codex/shared-skills")),
    ("claude", Path("plugins/claude/shared-skills")),
)

SHARED_SUBAGENT_ROOTS = (
    ("codex", Path("plugins/codex/shared-subagents"), ".toml"),
    ("claude", Path("plugins/claude/shared-subagents"), ".md"),
)


def validate_workflow_plugins(root: Path) -> list[str]:
    """Validate required workflow plugin artifacts by generated path structure."""

    errors: list[str] = []
    errors.extend(_validate_no_legacy_artifacts(root))
    errors.extend(_validate_required_shared_skill_references(root))
    errors.extend(_validate_required_shared_subagents(root))
    return errors


def _validate_no_legacy_artifacts(root: Path) -> list[str]:
    errors: list[str] = []
    generated_roots = [path for _, path in SHARED_SKILL_ROOTS] + [
        path for _, path, _ in SHARED_SUBAGENT_ROOTS
    ]

    for generated_root in generated_roots:
        absolute_root = root / generated_root
        if not absolute_root.exists():
            continue
        for path in absolute_root.rglob("*"):
            if not path.exists():
                continue
            relative_path = path.relative_to(root).as_posix()
            legacy_name = next(
                (name for name in FORBIDDEN_LEGACY_NAMES if name in path.parts),
                None,
            )
            if legacy_name is not None:
                errors.append(
                    "legacy generated artifact found: "
                    f"{relative_path} contains {legacy_name}"
                )

    return errors


def _validate_required_shared_skill_references(root: Path) -> list[str]:
    errors: list[str] = []

    for harness, relative_root in SHARED_SKILL_ROOTS:
        references_root = root / relative_root / "references"
        for reference in REQUIRED_SHARED_SKILL_REFERENCES:
            path = references_root / reference
            if not path.is_file():
                errors.append(
                    "missing required shared-skills reference "
                    f"for {harness}: {path.relative_to(root).as_posix()}"
                )

    return errors


def _validate_required_shared_subagents(root: Path) -> list[str]:
    errors: list[str] = []

    for harness, relative_root, suffix in SHARED_SUBAGENT_ROOTS:
        agents_root = root / relative_root / "agents"
        for agent in REQUIRED_SHARED_SUBAGENTS:
            path = agents_root / f"{agent}{suffix}"
            if not path.is_file():
                errors.append(
                    "missing required shared-subagents agent "
                    f"for {harness}: {path.relative_to(root).as_posix()}"
                )

    return errors
