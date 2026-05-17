"""Detect session-memory AGENTS.md rules and render install guidance."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Union


SECTION_HEADING = "## Codex Session Memory"
REQUIRED_SECTION_MARKER = SECTION_HEADING

REQUIRED_BLOCK_EN = """## Codex Session Memory

- Before ending a work turn, run `$session-memory:checkpoint` when there are changes, decisions, verification results, or remaining tasks to preserve.
- During long work or when MCP/tool usage consumes substantial context, run an intermediate `$session-memory:checkpoint`.
- Immediately after manual or automatic context compaction in the same Codex session, run `$session-memory:resume <current-session-prefix>` as the first action in the next turn.
- Do not auto-resume old sessions when starting a new session. Only resume when the user explicitly calls `$session-memory:resume <prefix>`.
- If the session state is unclear, run `$session-memory:status`.
- If `CODEX_SESSION_ID` is missing, do not checkpoint; report it.
- Use `CODEX_THREAD_ID` only to locate the active Codex rollout transcript, not as the session-memory artifact destination.
- Do not commit `.codex/` session data.
"""

REQUIRED_BLOCK_KO = """## Codex Session Memory

- 작업 턴을 끝내기 전에 변경 사항, 결정 사항, 검증 결과, 남은 작업이 있으면 `$session-memory:checkpoint`를 실행한다.
- 작업이 길어지거나 MCP/tool 사용으로 컨텍스트 소모가 커지면 중간 `$session-memory:checkpoint`를 실행한다.
- 같은 Codex 세션에서 수동 또는 자동 컨텍스트 압축이 발생한 직후 다음 턴에서는 `$session-memory:resume <current-session-prefix>`를 첫 행동으로 실행한다.
- 새 세션에서 과거 세션을 이어받는 경우에는 자동 resume하지 않는다. 사용자가 직접 `$session-memory:resume <prefix>`를 호출한다.
- 상태가 불확실하면 `$session-memory:status`를 실행한다.
- `CODEX_SESSION_ID`가 없으면 checkpoint를 진행하지 않고 사용자에게 보고한다.
- `CODEX_THREAD_ID`는 활성 Codex rollout transcript를 찾는 데에만 사용하고 session-memory artifact 목적지로 쓰지 않는다.
- `.codex/` 세션 데이터는 커밋하지 않는다.
"""

REQUIRED_BLOCK = REQUIRED_BLOCK_EN


REQUIRED_MARKERS = (
    "$session-memory:checkpoint",
    "$session-memory:resume",
    "$session-memory:status",
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    ".codex/",
)
REQUIRED_SEMANTIC_PATTERNS = (
    (
        "context compaction first-action resume rule",
        re.compile(
            r"context compaction.*\$session-memory:resume.*first action|"
            r"컨텍스트 압축.*\$session-memory:resume.*첫 행동",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "CODEX_SESSION_ID missing-env guard",
        re.compile(
            r"CODEX_SESSION_ID.*missing.*do not checkpoint|"
            r"CODEX_SESSION_ID.*없으면.*checkpoint를 진행하지",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "CODEX_THREAD_ID rollout lookup only",
        re.compile(
            r"CODEX_THREAD_ID.*rollout transcript.*not as the session-memory artifact destination|"
            r"CODEX_THREAD_ID.*rollout transcript.*artifact 목적지로 쓰지",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)

STALE_CODEX_THREAD_ID_GUARD = (
    "If `CODEX_THREAD_ID` is not available, do not checkpoint; "
    "report the missing session id to the user."
)
STALE_CODEX_THREAD_ID_GUARD_KO = "`CODEX_THREAD_ID`가 없으면 checkpoint를 진행하지 않고 사용자에게 보고한다."
STALE_CODEX_THREAD_ID_MISSING = "stale CODEX_THREAD_ID missing-env guard"
STALE_CODEX_THREAD_ID_GUARD_PATTERN = re.compile(
    r"CODEX_THREAD_ID.*(?:not available|missing).*do not checkpoint|"
    r"CODEX_THREAD_ID.*없으면.*checkpoint를 진행하지",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: tuple[str, ...]
    patch: str
    insert_after: str


def _missing_markers(text: str) -> tuple[str, ...]:
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    missing.extend(
        label for label, pattern in REQUIRED_SEMANTIC_PATTERNS if not pattern.search(text)
    )
    if (
        STALE_CODEX_THREAD_ID_GUARD in text
        or STALE_CODEX_THREAD_ID_GUARD_KO in text
        or STALE_CODEX_THREAD_ID_GUARD_PATTERN.search(text)
    ):
        missing.append(STALE_CODEX_THREAD_ID_MISSING)
    return tuple(missing)


def _missing_raw_markers(text: str) -> tuple[str, ...]:
    return tuple(marker for marker in REQUIRED_MARKERS if marker not in text)


def _codex_session_memory_section(text: str) -> Optional[str]:
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


def required_block(locale: Optional[str] = None) -> str:
    return REQUIRED_BLOCK_KO if locale == "ko" else REQUIRED_BLOCK_EN


def _patch_for(path: Path, locale: Optional[str] = None) -> str:
    return (
        f"AGENTS.md path: {path}\n\n"
        "Recommended insertion point: after the existing context/session-memory section, "
        "or near other workflow rules.\n\n"
        "Add this block:\n\n"
        f"{required_block(locale)}"
    )


def check_agents_rules(
    project_root: Union[str, Path], locale: Optional[str] = None
) -> RuleReport:
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

    full_file_raw_missing = _missing_raw_markers(text)
    if len(full_file_raw_missing) < len(REQUIRED_MARKERS):
        missing = full_file_raw_missing or (REQUIRED_SECTION_MARKER,)
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
        missing=_missing_markers(text),
        patch=_patch_for(agents_path, locale),
        insert_after="after existing context/session-memory rules",
    )
