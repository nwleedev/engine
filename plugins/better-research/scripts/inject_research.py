from pathlib import Path


_CORE_DEBIASING_CONTEXT = """\
<cognitive-debiasing>
Before responding, execute in order:
1. SUSPEND: Bracket any prior assumptions influencing this response.
2. ENUMERATE: List ALL available options before filtering any out.
3. MULTI-AXIS: Identify 2+ solution axes (not just "how" — also "when", "who", "what triggers").
4. VERIFY: Do your options cover the full option space?
5. COUNTER: Assume your leading approach is wrong. State at least one reason why.
   Adjust or explicitly confirm after examining the objection.
6. EVALUATE: Select using ONLY correctness, standard compliance, and maintainability.
   Prohibited criteria: fewer changes / faster / more familiar / lower risk to you.
7. DECLARE: Root cause in one sentence. Confirm this is structural, not symptomatic.
</cognitive-debiasing>"""


def build_core_debiasing() -> str:
    return _CORE_DEBIASING_CONTEXT


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
