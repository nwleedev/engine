"""Detect codex-quality-guard AGENTS.md rules and render install guidance."""
from dataclasses import dataclass
from pathlib import Path


SECTION_HEADING = "## Codex Quality Guard"

RECOMMENDED_BLOCK = """## Codex Quality Guard

- Before ending each work turn, check for superficial work using `codex-quality-guard:retrospect`.
- On turns with code or file changes, include changed files, verification run, and skipped checks as evidence.
- If `Superficial risk` is `medium`, `high`, or `unknown`, do not report completion; provide one concrete next action.
- If context was compacted or evidence is incomplete, inspect the visible request, AGENTS.md, changed files, project artifacts, and git status/diff before running `retrospect`.
- Session memory or separate notes may be used only as supporting evidence. Do not skip the check when they are unavailable.
- This process does not replace Codex `/review`. `/review` reviews diffs; `retrospect` reviews the current turn's working pattern.
"""

RECOMMENDED_BLOCK_KO = RECOMMENDED_BLOCK

REQUIRED_MARKER_GROUPS = (
    ("codex-quality-guard:retrospect", ("codex-quality-guard:retrospect",)),
    ("Superficial risk", ("Superficial risk",)),
    ("medium", ("medium",)),
    ("high", ("high",)),
    ("unknown", ("unknown",)),
    ("AGENTS.md", ("AGENTS.md",)),
    ("git status", ("git status",)),
    ("session memory", ("session memory", "Session memory")),
    ("/review", ("/review",)),
)


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: tuple[str, ...]
    guidance: str


def recommended_block(locale: str | None = None) -> str:
    return RECOMMENDED_BLOCK


def _section(text: str) -> str | None:
    lines = text.splitlines()
    section_lines: list[str] = []
    in_section = False

    for line in lines:
        stripped = line.strip()
        if stripped == SECTION_HEADING:
            in_section = True
            section_lines = [line]
            continue
        if in_section and stripped.startswith("#") and not stripped.startswith("###"):
            break
        if in_section:
            section_lines.append(line)

    if not in_section:
        return None

    return "\n".join(section_lines)


def _marker_label(group: tuple[str, tuple[str, ...]]) -> str:
    return group[0]


def _missing_markers_for_groups(
    text: str, groups: tuple[tuple[str, tuple[str, ...]], ...]
) -> tuple[str, ...]:
    missing = []
    for group in groups:
        label, alternatives = group
        if not any(marker in text for marker in alternatives):
            missing.append(label)
    return tuple(missing)


def _missing_markers(text: str) -> tuple[str, ...]:
    return _missing_markers_for_groups(text, REQUIRED_MARKER_GROUPS)


def _guidance_for(path: Path, locale: str | None = None) -> str:
    return (
        f"AGENTS.md path: {path}\n\n"
        "Recommended insertion point: near other workflow or final-response rules.\n\n"
        "Add this block:\n\n"
        f"{recommended_block(locale)}"
    )


def check_agents_rules(project_root: str | Path, locale: str | None = None) -> RuleReport:
    root = Path(project_root)
    agents_path = root / "AGENTS.md"
    guidance = _guidance_for(agents_path, locale)

    if not agents_path.is_file():
        return RuleReport(
            status="not found",
            agents_path=agents_path,
            missing=tuple(_marker_label(group) for group in REQUIRED_MARKER_GROUPS),
            guidance=guidance,
        )

    text = agents_path.read_text(encoding="utf-8")
    section = _section(text)
    if section is not None:
        missing = _missing_markers(section)
        if missing:
            return RuleReport(
                status="partial",
                agents_path=agents_path,
                missing=missing,
                guidance=guidance,
            )

        return RuleReport(
            status="installed",
            agents_path=agents_path,
            missing=(),
            guidance="",
        )

    full_file_missing = _missing_markers(text)
    non_path_markers = tuple(
        group for group in REQUIRED_MARKER_GROUPS if _marker_label(group) != "AGENTS.md"
    )
    non_path_missing = _missing_markers_for_groups(text, non_path_markers)
    if len(non_path_missing) < len(non_path_markers):
        return RuleReport(
            status="partial",
            agents_path=agents_path,
            missing=full_file_missing,
            guidance=guidance,
        )

    return RuleReport(
        status="missing",
        agents_path=agents_path,
        missing=full_file_missing,
        guidance=guidance,
    )
