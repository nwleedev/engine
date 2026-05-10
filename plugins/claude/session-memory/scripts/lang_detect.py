import json
import os
from pathlib import Path

SUPPORTED = {"ko", "en"}
DEFAULT = "en"


def detect(cwd: str) -> str:
    """Return language code for context file content.

    Priority: settings.local.json → settings.json → OS LANG → 'en'.
    Unsupported languages fall back to DEFAULT.
    """
    lang = _from_settings(cwd) or _from_os_env()
    return lang if lang in SUPPORTED else DEFAULT


def _from_settings(cwd: str) -> str:
    claude_dir = Path(cwd) / ".claude"
    for filename in ("settings.local.json", "settings.json"):
        path = claude_dir / filename
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lang = data.get("env", {}).get("SESSION_MEMORY_LANG", "")
            if lang:
                return lang.lower().strip()
        except Exception:
            continue
    return ""


def _from_os_env() -> str:
    lang_env = os.environ.get("LANG", "")
    if not lang_env:
        return ""
    return lang_env.split("_")[0].split(".")[0].lower()
