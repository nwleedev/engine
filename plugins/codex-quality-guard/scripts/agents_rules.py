"""Detect codex-quality-guard AGENTS.md rules and render install guidance."""
from dataclasses import dataclass
from pathlib import Path


SECTION_HEADING = "## Codex Quality Guard"

RECOMMENDED_BLOCK = """## Codex Quality Guard

- Before finalizing a work turn, run `git status --short` and inspect the relevant diff so completion claims match the current worktree.
- Run `$codex-quality-guard:retrospect` before the final response when the turn included code changes, file edits, verification results, or implementation decisions.
- Use session memory or an equivalent context record when decisions, verification results, or remaining tasks need to survive context compaction.
- Treat missing verification, skipped tests without a concrete reason, or unsupported done claims as issues to resolve before reporting completion.
"""

RECOMMENDED_BLOCK_KO = """## Codex Quality Guard

- 작업 턴을 끝내기 전에 `git status --short`를 실행하고 관련 diff를 확인해 완료 보고가 현재 작업트리와 일치하는지 검증한다.
- 코드 변경, 파일 수정, 검증 결과, 구현 결정이 있었던 턴에서는 최종 답변 전에 `$codex-quality-guard:retrospect`를 실행한다.
- 결정 사항, 검증 결과, 남은 작업이 컨텍스트 압축 이후에도 유지되어야 하면 세션 메모리 또는 동등한 컨텍스트 기록을 사용한다.
- 검증 누락, 구체적 이유 없는 테스트 생략, 근거 없는 완료 주장은 완료 보고 전에 해결해야 할 문제로 취급한다.
"""

REQUIRED_MARKER_GROUPS = (
    ("section heading", (SECTION_HEADING,)),
    ("git status", ("git status --short", "git status")),
    ("retrospect skill", ("$codex-quality-guard:retrospect",)),
    ("session memory", ("session memory", "세션 메모리", "context record", "컨텍스트 기록")),
    ("verification", ("verification", "검증")),
)


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: tuple[str, ...]
    guidance: str


def recommended_block(locale: str | None = None) -> str:
    return RECOMMENDED_BLOCK_KO if locale == "ko" else RECOMMENDED_BLOCK


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


def _missing_markers(text: str) -> tuple[str, ...]:
    missing = []
    for group in REQUIRED_MARKER_GROUPS:
        label, alternatives = group
        if not any(marker in text for marker in alternatives):
            missing.append(label)
    return tuple(missing)


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
    if len(full_file_missing) < len(REQUIRED_MARKER_GROUPS):
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
