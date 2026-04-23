import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from session_state import get_flag_path, deactivate, get_textbooks_dir


def find_project_root(cwd: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    path = Path(cwd)
    for candidate in [path] + list(path.parents):
        if (candidate / ".claude").is_dir():
            return str(candidate)
    return cwd


def resolve_cwd(payload: dict) -> str:
    cwd = payload.get("cwd", "")
    if cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR", os.environ.get("PWD", ""))


def build_toc_context(textbooks_dir: Path) -> str:
    if not textbooks_dir.exists():
        return ""
    parts = ["## Textbooks", ""]
    found = False
    for domain_dir in sorted(textbooks_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        concepts = [p for p in domain_dir.rglob("*.md") if p.name != "INDEX.md"]
        if not concepts:
            continue
        stage = "01-overview"
        for p in concepts:
            p_str = str(p)
            if "03-advanced" in p_str:
                stage = "03-advanced"
                break
            elif "02-core-concepts" in p_str:
                stage = "02-core-concepts"
        count = len(concepts)
        concept_label = "concept" if count == 1 else "concepts"
        parts.append(f"- {domain_dir.name}: {count} {concept_label} (up to {stage})")
        found = True
    if not found:
        return ""
    return "\n".join(parts)


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    cwd = resolve_cwd(payload)
    if not cwd:
        return
    project_root = find_project_root(cwd)

    flag = get_flag_path(payload, project_root)
    if flag is not None:
        deactivate(flag)

    textbooks_dir = get_textbooks_dir(project_root)
    context = build_toc_context(textbooks_dir)
    if not context:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
