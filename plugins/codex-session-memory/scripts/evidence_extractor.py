"""Extract durable facts from Codex transcript deltas without an LLM."""
import re


FILE_RE = re.compile(r"[\w./-]+\.(?:py|json|md|toml|yaml|yml|ts|tsx|js|jsx)")
COMMAND_WORDS = r"(?:pytest|git|codex|python|pnpm|npm)"
INLINE_COMMAND_RE = re.compile(rf"(?<!`)`(?!`)([^`\n]*(?:{COMMAND_WORDS})[^`\n]*)`(?!`)")
FENCED_COMMAND_RE = re.compile(r"```(?:bash|shell|sh)?\n(.*?)```", re.DOTALL)
PLAIN_COMMAND_RE = re.compile(rf"^\s*(?:\$\s*)?({COMMAND_WORDS}\b[^\n`]*)\s*$", re.MULTILINE)
URL_RE = re.compile(r"https?://[^\s)]+")
FAIL_RE = re.compile(r"^(?:FAIL|FAILED|ERROR|Error:|fatal:).*$", re.MULTILINE)
TRAILING_URL_PUNCTUATION = ".,`\"']}>;:"


def _unique(items):
    seen = set()
    out = []
    for item in items:
        cleaned = item.strip().rstrip(".,")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def _clean_url(url: str) -> str:
    return url.strip().rstrip(TRAILING_URL_PUNCTUATION)


def _extract_commands(text: str) -> list[str]:
    commands = []
    for match in INLINE_COMMAND_RE.finditer(text):
        commands.append((match.start(1), match.group(1)))

    for match in FENCED_COMMAND_RE.finditer(text):
        block = match.group(1)
        block_start = match.start(1)
        for command_match in PLAIN_COMMAND_RE.finditer(block):
            commands.append((block_start + command_match.start(1), command_match.group(1)))

    for match in PLAIN_COMMAND_RE.finditer(text):
        commands.append((match.start(1), match.group(1)))

    return _unique(command for _, command in sorted(commands))


def extract_evidence(delta: list[dict]) -> dict:
    text = "\n".join(str(item.get("text", "")) for item in delta)
    sources = _unique(_clean_url(url) for url in URL_RE.findall(text))
    text_without_urls = URL_RE.sub("", text)
    return {
        "files": _unique(FILE_RE.findall(text_without_urls))[:40],
        "commands": _extract_commands(text)[:30],
        "failures": _unique(FAIL_RE.findall(text))[:20],
        "sources": sources[:30],
    }
