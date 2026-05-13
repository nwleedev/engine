"""Detect quality-guard AGENTS.md rules and render install guidance."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


SECTION_HEADING = "## Codex Quality Guard"

RECOMMENDED_BLOCK = """## Codex Quality Guard

- Before ending each work turn, check for superficial work using `quality-guard:retrospect`.
- On turns with code or file changes, include changed files, verification run, and skipped checks as evidence.
- If `Superficial risk` is `medium`, `high`, or `unknown`, do not report completion; provide one concrete next action.
- If context was compacted or evidence is incomplete, inspect the visible request, AGENTS.md, changed files, project artifacts, and git status/diff before running `retrospect`.
- Session memory or separate notes may be used only as supporting evidence. Do not skip the check when they are unavailable.
- This process does not replace Codex `/review`. `/review` reviews diffs; `retrospect` reviews the current turn's working pattern.
"""

RECOMMENDED_BLOCK_KO = """## Codex Quality Guard

- 각 작업 턴을 마치기 전에 `quality-guard:retrospect` 기준으로 superficial 작업 여부를 점검한다.
- 코드 변경이 있는 턴에서는 변경 파일, 실행한 검증, 생략된 확인을 근거로 남긴다.
- `Superficial risk`가 `medium`, `high`, `unknown`이면 완료로 보고하지 말고 한 가지 다음 조치를 제시한다.
- 컨텍스트 압축이 발생했거나 근거가 부족하면 현재 대화에서 보이는 요청, AGENTS.md, 변경 파일, 작업 산출물, git 상태와 diff를 먼저 확인한 뒤 `retrospect`를 수행한다.
- 세션 메모리나 별도 기록 파일이 있는 경우에는 보조 근거로만 참고하며, 없다는 이유로 점검을 생략하지 않는다.
- 이 절차는 Codex `/review`를 대체하지 않는다. `/review`는 diff 리뷰이고, `retrospect`는 현재 턴의 작업 방식 회고다.
"""

REQUIRED_MARKER_GROUPS = (
    ("quality-guard:retrospect", ("quality-guard:retrospect",)),
    ("Superficial risk", ("Superficial risk",)),
    ("medium", ("medium",)),
    ("high", ("high",)),
    ("unknown", ("unknown",)),
    ("AGENTS.md", ("AGENTS.md",)),
    ("git status", ("git status", "git 상태")),
    ("session memory", ("session memory", "Session memory", "세션 메모리")),
    ("/review", ("/review",)),
)


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: tuple[str, ...]
    guidance: str


def recommended_block(locale: Optional[str] = None) -> str:
    return RECOMMENDED_BLOCK_KO if locale == "ko" else RECOMMENDED_BLOCK


def _section(text: str) -> Optional[str]:
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


def _guidance_for(path: Path, locale: Optional[str] = None) -> str:
    return (
        f"AGENTS.md path: {path}\n\n"
        "Recommended insertion point: near other workflow or final-response rules.\n\n"
        "Add this block:\n\n"
        f"{recommended_block(locale)}"
    )


def check_agents_rules(
    project_root: Union[str, Path], locale: Optional[str] = None
) -> RuleReport:
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
