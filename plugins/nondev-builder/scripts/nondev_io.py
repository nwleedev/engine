import json
from datetime import date
from pathlib import Path

_NONDEV_DIR = ".claude/nondev"
_COMMANDS_DIR = ".claude/commands"
_INDEX_FILE = ".claude/nondev/index.json"


def _index_path(cwd: str) -> Path:
    return Path(cwd) / _INDEX_FILE


def _skill_path(cwd: str, task_name: str) -> Path:
    return Path(cwd) / _NONDEV_DIR / task_name / "skill.md"


def _rubric_path(cwd: str, task_name: str) -> Path:
    return Path(cwd) / _NONDEV_DIR / task_name / "rubric.md"


def ensure_dirs(cwd: str, task_name: str) -> None:
    (Path(cwd) / _NONDEV_DIR / task_name).mkdir(parents=True, exist_ok=True)
    (Path(cwd) / _COMMANDS_DIR).mkdir(parents=True, exist_ok=True)


def read_index(cwd: str) -> dict | None:
    p = _index_path(cwd)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def upsert_domain(cwd: str, domain_entry: dict) -> None:
    p = _index_path(cwd)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        try:
            index = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = {"version": "1", "domains": []}
    else:
        index = {"version": "1", "domains": []}

    task_name = domain_entry["task_name"]
    domains = index.get("domains", [])
    for i, d in enumerate(domains):
        if d.get("task_name") == task_name:
            domains[i] = domain_entry
            break
    else:
        domains.append(domain_entry)

    index["domains"] = domains
    index["updated"] = date.today().isoformat()
    p.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def read_skill(cwd: str, task_name: str) -> str | None:
    p = _skill_path(cwd, task_name)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def write_skill(cwd: str, task_name: str, content: str) -> None:
    p = _skill_path(cwd, task_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def read_rubric(cwd: str, task_name: str) -> str | None:
    p = _rubric_path(cwd, task_name)
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def write_rubric(cwd: str, task_name: str, content: str) -> None:
    p = _rubric_path(cwd, task_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
