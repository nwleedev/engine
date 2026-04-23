import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from inject_toc import find_project_root, resolve_cwd
from session_state import get_flag_path, is_active, activate, deactivate


def main_with_payload(payload: dict) -> str:
    cwd = resolve_cwd(payload)
    if not cwd:
        return "inactive"
    project_root = find_project_root(cwd)
    flag = get_flag_path(payload, project_root)
    if flag is None:
        return "inactive"
    if is_active(flag):
        deactivate(flag)
        return "inactive"
    activate(flag)
    return "active"


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        payload = {}
    print(main_with_payload(payload))


if __name__ == "__main__":
    main()
