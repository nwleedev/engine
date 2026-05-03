"""Detect codex-session-memory AGENTS.md rules and render install guidance."""
from dataclasses import dataclass
from pathlib import Path


REQUIRED_BLOCK = """## Codex Session Memory

- 작업 턴을 끝내기 전에 변경 사항, 결정 사항, 검증 결과, 남은 작업이 있으면 `$codex-session-memory:checkpoint`를 실행한다.
- 작업이 길어지거나 MCP/tool 사용으로 컨텍스트 소모가 커지면 중간 `$codex-session-memory:checkpoint`를 실행한다.
- 같은 Codex 세션에서 수동 또는 자동 컨텍스트 압축이 발생한 직후 다음 턴에서는 `$codex-session-memory:resume <current-session-prefix>`를 첫 행동으로 실행한다.
- 새 세션에서 과거 세션을 이어받는 경우에는 자동 resume하지 않는다. 사용자가 직접 `$codex-session-memory:resume <prefix>`를 호출한다.
- 상태가 불확실하면 `$codex-session-memory:status`를 실행한다.
- `CODEX_THREAD_ID`가 없으면 checkpoint를 진행하지 않고 사용자에게 보고한다.
- `.codex/` 세션 데이터는 커밋하지 않는다.
"""


REQUIRED_MARKERS = [
    "$codex-session-memory:checkpoint",
    "$codex-session-memory:resume",
    "$codex-session-memory:status",
    "CODEX_THREAD_ID",
    ".codex/",
    "컨텍스트 압축",
    "첫 행동",
]


@dataclass(frozen=True)
class RuleReport:
    status: str
    agents_path: Path
    missing: list[str]
    patch: str
    insert_after: str


def _missing_markers(text: str) -> list[str]:
    return [marker for marker in REQUIRED_MARKERS if marker not in text]


def _patch_for(path: Path) -> str:
    return (
        f"AGENTS.md path: {path}\n\n"
        "Recommended insertion point: after the existing context/session-memory section, "
        "or near other workflow rules.\n\n"
        "Add this block:\n\n"
        f"{REQUIRED_BLOCK}"
    )


def check_agents_rules(project_root: str | Path) -> RuleReport:
    root = Path(project_root)
    agents_path = root / "AGENTS.md"
    if not agents_path.is_file():
        return RuleReport(
            status="not found",
            agents_path=agents_path,
            missing=REQUIRED_MARKERS[:],
            patch=_patch_for(agents_path),
            insert_after="create AGENTS.md at project root",
        )

    text = agents_path.read_text(encoding="utf-8")
    missing = _missing_markers(text)
    if not missing:
        return RuleReport(
            status="installed",
            agents_path=agents_path,
            missing=[],
            patch="",
            insert_after="",
        )

    return RuleReport(
        status="partial" if len(missing) < len(REQUIRED_MARKERS) else "missing",
        agents_path=agents_path,
        missing=missing,
        patch=_patch_for(agents_path),
        insert_after="after existing context/session-memory rules",
    )
