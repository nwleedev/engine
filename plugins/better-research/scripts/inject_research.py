import re
from pathlib import Path

_DESIGN_KEYWORD_RE = re.compile(
    r'(설계|방법|접근법|구현|어떻게|전략|design|approach|architect|implement|strategy)',
    re.IGNORECASE,
)

_ANTI_FRAME_BIAS_CONTEXT = """\
<cognitive-debiasing>
Before responding, execute in order:
1. SUSPEND: Declare any prior-session assumptions influencing this response, then bracket them.
2. ENUMERATE: List ALL available primitives/components in this domain before filtering.
3. MULTI-AXIS: Identify 2+ solution axes (not just "how" — also "when", "who", "what triggers").
4. VERIFY: Do your options cover the full primitive list? If not, reconstruct.
</cognitive-debiasing>"""


def build_anti_frame_bias_context() -> str:
    return _ANTI_FRAME_BIAS_CONTEXT


def detect_design_keyword(prompt: str) -> bool:
    return bool(_DESIGN_KEYWORD_RE.search(prompt))


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
