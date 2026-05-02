"""Extract durable facts from Codex transcript deltas without an LLM."""
import re


FILE_RE = re.compile(r"[\w./-]+\.(?:py|json|md|toml|yaml|yml|ts|tsx|js|jsx)")
COMMAND_RE = re.compile(r"`([^`]*(?:pytest|git|codex|python|pnpm|npm)[^`]*)`")
URL_RE = re.compile(r"https?://[^\s)]+")
FAIL_RE = re.compile(r"^(?:FAIL|FAILED|ERROR|Error:|fatal:).*$", re.MULTILINE)


def _unique(items):
    seen = set()
    out = []
    for item in items:
        cleaned = item.strip().rstrip(".,")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def extract_evidence(delta: list[dict]) -> dict:
    text = "\n".join(str(item.get("text", "")) for item in delta)
    return {
        "files": _unique(FILE_RE.findall(text))[:40],
        "commands": _unique(COMMAND_RE.findall(text))[:30],
        "failures": _unique(FAIL_RE.findall(text))[:20],
        "sources": _unique(URL_RE.findall(text))[:30],
    }
