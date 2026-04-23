from pathlib import Path

_SESSIONS_DIR = ".claude/sessions"
_TEXTBOOKS_DIR = ".claude/textbooks"
_FLAG_NAME = ".professor-active"
_SKILL_MD_PATH = Path(__file__).parent.parent / "skills" / "domain-professor" / "SKILL.md"
_TRANSCRIPT_WINDOW = 20
_TRANSCRIPT_MAX_CHARS = 4000


def get_flag_path(payload: dict, project_root: str) -> "Path | None":
    session_id = payload.get("session_id", "")
    if not session_id:
        transcript = payload.get("transcript_path", "")
        if transcript:
            session_id = Path(transcript).parent.name
    if not session_id:
        return None
    return Path(project_root) / _SESSIONS_DIR / session_id / _FLAG_NAME


def is_active(flag: "Path | None") -> bool:
    return flag is not None and flag.exists()


def activate(flag: Path) -> None:
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.touch()


def deactivate(flag: Path) -> None:
    flag.unlink(missing_ok=True)


def read_skill_content() -> str:
    try:
        return _SKILL_MD_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def get_textbooks_dir(project_root: str) -> Path:
    return Path(project_root) / _TEXTBOOKS_DIR
