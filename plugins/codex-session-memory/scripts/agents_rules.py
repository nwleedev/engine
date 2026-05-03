"""Detect codex-session-memory AGENTS.md rules and render install guidance."""
from dataclasses import dataclass
from pathlib import Path


SECTION_HEADING = "## Codex Session Memory"
REQUIRED_SECTION_MARKER = SECTION_HEADING

REQUIRED_BLOCK_EN = """## Codex Session Memory

- Before ending a work turn, run `$codex-session-memory:checkpoint` when there are changes, decisions, verification results, or remaining tasks to preserve.
- During long work or when MCP/tool usage consumes substantial context, run an intermediate `$codex-session-memory:checkpoint`.
- Immediately after manual or automatic context compaction in the same Codex session, run `$codex-session-memory:resume <current-session-prefix>` as the first action in the next turn.
- Do not auto-resume old sessions when starting a new session. Only resume when the user explicitly calls `$codex-session-memory:resume <prefix>`.
- If the session state is unclear, run `$codex-session-memory:status`.
- If `CODEX_THREAD_ID` is not available, do not checkpoint; report the missing session id to the user.
- Do not commit `.codex/` session data.
"""

REQUIRED_BLOCK_KO = """## Codex Session Memory

- 작업 턴을 끝내기 전에 변경 사항, 결정 사항, 검증 결과, 남은 작업이 있으면 `$codex-session-memory:checkpoint`를 실행한다.
- 작업이 길어지거나 MCP/tool 사용으로 컨텍스트 소모가 커지면 중간 `$codex-session-memory:checkpoint`를 실행한다.
- 같은 Codex 세션에서 수동 또는 자동 컨텍스트 압축이 발생한 직후 다음 턴에서는 `$codex-session-memory:resume <current-session-prefix>`를 첫 행동으로 실행한다.
- 새 세션에서 과거 세션을 이어받는 경우에는 자동 resume하지 않는다. 사용자가 직접 `$codex-session-memory:resume <prefix>`를 호출한다.
- 상태가 불확실하면 `$codex-session-memory:status`를 실행한다.
- `CODEX_THREAD_ID`가 없으면 checkpoint를 진행하지 않고 사용자에게 보고한다.
- `.codex/` 세션 데이터는 커밋하지 않는다.
"""

REQUIRED_BLOCK = REQUIRED_BLOCK_EN


REQUIRED_MARKERS = (
    "$codex-session-memory:checkpoint",
    "$codex-session-memory:resume",
    "$codex-session-memory:status",
    "CODEX_THREAD_ID",
    ".codex/",
)


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: tuple[str, ...]
    patch: str
    insert_after: str


def _missing_markers(text: str) -> tuple[str, ...]:
    return tuple(marker for marker in REQUIRED_MARKERS if marker not in text)


def _codex_session_memory_section(text: str) -> str | None:
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


def required_block(locale: str | None = None) -> str:
    return REQUIRED_BLOCK_KO if locale == "ko" else REQUIRED_BLOCK_EN


def _patch_for(path: Path, locale: str | None = None) -> str:
    return (
        f"AGENTS.md path: {path}\n\n"
        "Recommended insertion point: after the existing context/session-memory section, "
        "or near other workflow rules.\n\n"
        "Add this block:\n\n"
        f"{required_block(locale)}"
    )


def check_agents_rules(project_root: str | Path, locale: str | None = None) -> RuleReport:
    root = Path(project_root)
    agents_path = root / "AGENTS.md"
    if not agents_path.is_file():
        return RuleReport(
            status="not found",
            agents_path=agents_path,
            missing=REQUIRED_MARKERS,
            patch=_patch_for(agents_path, locale),
            insert_after="create AGENTS.md at project root",
        )

    text = agents_path.read_text(encoding="utf-8")
    section = _codex_session_memory_section(text)
    if section is not None:
        missing = _missing_markers(section)
        if missing:
            return RuleReport(
                status="partial",
                agents_path=agents_path,
                missing=missing,
                patch=_patch_for(agents_path, locale),
                insert_after="after existing context/session-memory rules",
            )

        return RuleReport(
            status="installed",
            agents_path=agents_path,
            missing=(),
            patch="",
            insert_after="",
        )

    full_file_missing = _missing_markers(text)
    if len(full_file_missing) < len(REQUIRED_MARKERS):
        missing = full_file_missing or (REQUIRED_SECTION_MARKER,)
        return RuleReport(
            status="partial",
            agents_path=agents_path,
            missing=missing,
            patch=_patch_for(agents_path, locale),
            insert_after="after existing context/session-memory rules",
        )

    return RuleReport(
        status="missing",
        agents_path=agents_path,
        missing=full_file_missing,
        patch=_patch_for(agents_path, locale),
        insert_after="after existing context/session-memory rules",
    )
