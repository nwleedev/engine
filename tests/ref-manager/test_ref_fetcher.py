import shutil
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/ref-manager/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import ref_fetcher


# ── detect_input_type ────────────────────────────────────────────────────────

def test_detect_input_type_http():
    assert ref_fetcher.detect_input_type("http://example.com") == "url"


def test_detect_input_type_https():
    assert ref_fetcher.detect_input_type("https://docs.python.org/3/library/typing.html") == "url"


def test_detect_input_type_file_path():
    assert ref_fetcher.detect_input_type("/home/user/Downloads/report.pdf") == "file"


def test_detect_input_type_relative_path():
    assert ref_fetcher.detect_input_type("./report.md") == "file"


# ── slugify ──────────────────────────────────────────────────────────────────

def test_slugify_basic():
    assert ref_fetcher.slugify("Python Typing Docs") == "python-typing-docs"


def test_slugify_removes_special_chars():
    slug = ref_fetcher.slugify("Hello! World (2024)")
    assert " " not in slug
    assert "!" not in slug
    assert "(" not in slug
    assert ")" not in slug


def test_slugify_collapses_hyphens():
    slug = ref_fetcher.slugify("foo  --  bar")
    assert "--" not in slug
    assert slug == "foo-bar"


def test_slugify_strips_leading_trailing_hyphens():
    slug = ref_fetcher.slugify("  leading trailing  ")
    assert not slug.startswith("-")
    assert not slug.endswith("-")


# ── copy_file ────────────────────────────────────────────────────────────────

def test_copy_file_pdf(tmp_path):
    src = tmp_path / "report.pdf"
    src.write_bytes(b"%PDF-1.4 test")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    result = ref_fetcher.copy_file(str(src), dest_dir)
    assert result.exists()
    assert result.suffix == ".pdf"
    assert result.read_bytes() == b"%PDF-1.4 test"


def test_copy_file_md(tmp_path):
    src = tmp_path / "notes.md"
    src.write_text("# Notes\nHello", encoding="utf-8")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    result = ref_fetcher.copy_file(str(src), dest_dir)
    assert result.exists()
    assert result.suffix == ".md"


def test_copy_file_txt(tmp_path):
    src = tmp_path / "readme.txt"
    src.write_text("Some text", encoding="utf-8")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    result = ref_fetcher.copy_file(str(src), dest_dir)
    assert result.exists()
    assert result.suffix == ".txt"


def test_copy_file_rejects_unsupported_extension(tmp_path):
    src = tmp_path / "script.py"
    src.write_text("print('hi')", encoding="utf-8")
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    import pytest
    with pytest.raises(ValueError, match="Unsupported"):
        ref_fetcher.copy_file(str(src), dest_dir)


def test_copy_file_creates_dest_dir(tmp_path):
    src = tmp_path / "doc.md"
    src.write_text("# Doc", encoding="utf-8")
    dest_dir = tmp_path / "new_dir" / "nested"
    result = ref_fetcher.copy_file(str(src), dest_dir)
    assert result.exists()


# ── fetch_url ────────────────────────────────────────────────────────────────

def _make_mock_response(content_type: str, content: bytes, url: str = "https://example.com/page"):
    """Build a mock urllib response."""
    resp = mock.MagicMock()
    resp.headers = mock.MagicMock()
    resp.headers.get = mock.MagicMock(return_value=content_type)
    resp.read = mock.MagicMock(return_value=content)
    resp.__enter__ = mock.MagicMock(return_value=resp)
    resp.__exit__ = mock.MagicMock(return_value=False)
    return resp


def test_fetch_url_html_saves_md_and_html(tmp_path):
    html = b"<html><body><h1>Hello</h1><p>World</p></body></html>"
    resp = _make_mock_response("text/html; charset=utf-8", html)
    with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
        result = ref_fetcher.fetch_url("https://example.com/page", tmp_path)
    assert result.exists()
    assert result.suffix == ".md"
    content = result.read_text(encoding="utf-8")
    assert "Hello" in content
    # Original HTML must also be saved
    html_path = result.with_suffix(".html")
    assert html_path.exists()
    assert b"<h1>Hello</h1>" in html_path.read_bytes()


def test_fetch_url_pdf_saves_raw_bytes(tmp_path):
    pdf_bytes = b"%PDF-1.4 binary content"
    resp = _make_mock_response("application/pdf", pdf_bytes)
    with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
        result = ref_fetcher.fetch_url("https://example.com/doc.pdf", tmp_path)
    assert result.exists()
    assert result.suffix == ".pdf"
    assert result.read_bytes() == pdf_bytes


def test_fetch_url_text_plain_saves_as_txt(tmp_path):
    text = b"Plain text content\nLine two"
    resp = _make_mock_response("text/plain", text)
    with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
        result = ref_fetcher.fetch_url("https://example.com/notes.txt", tmp_path)
    assert result.exists()
    assert result.suffix == ".txt"
    assert "Plain text content" in result.read_text(encoding="utf-8")


def test_fetch_url_creates_dest_dir(tmp_path):
    html = b"<html><body><p>hi</p></body></html>"
    resp = _make_mock_response("text/html", html)
    dest = tmp_path / "new" / "subdir"
    with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
        result = ref_fetcher.fetch_url("https://example.com/", dest)
    assert result.exists()
