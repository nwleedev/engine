from __future__ import annotations

import re
import shutil
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}


def detect_input_type(arg: str) -> str:
    if arg.startswith("http://") or arg.startswith("https://"):
        return "url"
    return "file"


def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    return slug


class _TextExtractor(HTMLParser):
    """Minimal HTML → plain text extractor using stdlib html.parser."""

    _SKIP_TAGS = {"script", "style", "head", "noscript", "nav", "footer"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._parts)


def _html_to_text(html_bytes: bytes) -> str:
    try:
        html_str = html_bytes.decode("utf-8")
    except UnicodeDecodeError:
        html_str = html_bytes.decode("latin-1")
    parser = _TextExtractor()
    parser.feed(html_str)
    return parser.get_text()


_MAX_FETCH_BYTES = 50 * 1024 * 1024  # 50 MB guard against runaway responses


def fetch_url(url: str, dest_dir: Path) -> Path:
    """Fetch URL and save to dest_dir.

    text/html        → save original as .html AND converted text as .md; return .md path
    application/pdf  → raw bytes → .pdf
    text/*           → raw text → .txt

    Returns the primary Path (for HTML: the .md file).
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(url)
    url_path = parsed.path.rstrip("/").rsplit("/", 1)[-1] or "index"
    base = slugify(url_path.rsplit(".", 1)[0]) or "page"

    with urllib.request.urlopen(url) as resp:  # noqa: S310
        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        raw = resp.read(_MAX_FETCH_BYTES)

    if content_type == "text/html":
        html_dest = dest_dir / f"{base}.html"
        html_dest.write_bytes(raw)
        md_dest = dest_dir / f"{base}.md"
        md_dest.write_text(_html_to_text(raw), encoding="utf-8")
        return md_dest
    elif content_type == "application/pdf":
        dest = dest_dir / f"{base}.pdf"
        dest.write_bytes(raw)
        return dest
    else:
        dest = dest_dir / f"{base}.txt"
        dest.write_text(raw.decode("utf-8", errors="replace"), encoding="utf-8")
        return dest


def copy_file(src: str, dest_dir: Path) -> Path:
    """Copy a local file to dest_dir. Only .pdf, .md, .txt are accepted."""
    src_path = Path(src)
    if src_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{src_path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src_path.name
    shutil.copy2(str(src_path), str(dest))
    return dest
