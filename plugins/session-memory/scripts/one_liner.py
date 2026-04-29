"""First-sentence extraction with abbreviation protection."""
import re

ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "cf.", "vs.", "Mr.", "Dr.", "Inc.", "Ltd.")
SENT_END = re.compile(r"[.。!?]")


def extract(text: str, max_len: int = 80) -> str:
    if not text:
        return ""
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", "\x00"))
    match = SENT_END.search(protected)
    if match:
        first = protected[: match.start()]
    else:
        first = protected
    first = first.replace("\x00", ".")
    return first.strip()[:max_len]
