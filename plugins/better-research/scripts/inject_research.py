from pathlib import Path


def load_skill_md(plugin_root: str) -> str:
    path = Path(plugin_root) / "skills" / "research-protocol" / "SKILL.md"
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def build_perspective_context(perspectives_str: str) -> str:
    perspectives = [p.strip() for p in perspectives_str.split(",") if p.strip()]
    if not perspectives:
        return ""
    joined = ", ".join(perspectives)
    return (
        f"Active research perspectives: {joined}\n"
        "Apply these lenses to every response in this session."
    )


def assemble_context(parts: list[str]) -> str:
    non_empty = [p for p in parts if p]
    return "\n\n---\n\n".join(non_empty)
