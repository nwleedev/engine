import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import handwrite_context as hw


def test_section_headers_ko():
    assert hw.SECTION_HEADERS["ko"]["what_why"] == "## 무엇을 왜"
    assert hw.SECTION_HEADERS["ko"]["decisions"] == "## 주요 결정"
    assert hw.SECTION_HEADERS["ko"]["incomplete"] == "## 미완료"
    assert hw.SECTION_HEADERS["ko"]["next_instructions"] == "## 다음 세션 지침"


def test_section_headers_en():
    assert hw.SECTION_HEADERS["en"]["what_why"] == "## What & Why"
    assert hw.SECTION_HEADERS["en"]["decisions"] == "## Key Decisions"
    assert hw.SECTION_HEADERS["en"]["incomplete"] == "## Incomplete"
    assert hw.SECTION_HEADERS["en"]["next_instructions"] == "## Instructions for Next Session"


def test_build_prompt_includes_language():
    prompt = hw.build_prompt("test conversation", False, "ko")
    assert "in ko" in prompt
    assert "test conversation" in prompt


def test_build_prompt_includes_truncation_note():
    prompt = hw.build_prompt("text", True, "en")
    assert "omitted" in prompt.lower() or "earlier" in prompt.lower()


def test_build_prompt_no_note_when_not_truncated():
    prompt = hw.build_prompt("text", False, "en")
    assert "omitted" not in prompt.lower()


# ── get_hourly_context_path ──────────────────────────────────────────

def test_hourly_path_new_file(tmp_path):
    session_dir = tmp_path / "session1"
    (session_dir / "contexts").mkdir(parents=True)
    path = hw.get_hourly_context_path(str(session_dir), "jwt-auth")
    assert path.name.startswith("CONTEXT-")
    assert "-jwt-auth.md" in path.name
    assert path.name.count("-") >= 3  # CONTEXT-YYYYMMDD-HH00-title


def test_hourly_path_reuses_existing(tmp_path):
    session_dir = tmp_path / "session1"
    contexts = session_dir / "contexts"
    contexts.mkdir(parents=True)
    from datetime import datetime
    prefix = "CONTEXT-" + datetime.utcnow().strftime("%Y%m%d-%H00-")
    existing = contexts / f"{prefix}first-title.md"
    existing.write_text("existing", encoding="utf-8")
    path = hw.get_hourly_context_path(str(session_dir), "second-title")
    assert path == existing


# ── write_context_file ───────────────────────────────────────────────

def _make_result(what_why="Done.", decisions=None, incomplete=None, next_inst="Check X."):
    return {
        "what_why": what_why,
        "decisions": decisions if decisions is not None else ["Used approach A (rejected B)"],
        "incomplete": incomplete if incomplete is not None else ["Item 1"],
        "next_instructions": next_inst,
    }


def test_write_creates_file_en(tmp_path):
    session_dir = tmp_path / "s1"
    (session_dir / "contexts").mkdir(parents=True)
    filename = hw.write_context_file(str(session_dir), "jwt-auth", "en", _make_result(), "abcdefgh")
    path = session_dir / "contexts" / filename
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "## What & Why" in content
    assert "## Key Decisions" in content
    assert "## Incomplete" in content
    assert "## Instructions for Next Session" in content
    assert "Done." in content
    assert "session: abcdefgh" in content


def test_write_creates_file_ko(tmp_path):
    session_dir = tmp_path / "s1"
    (session_dir / "contexts").mkdir(parents=True)
    filename = hw.write_context_file(str(session_dir), "jwt-auth", "ko", _make_result(), "abcdefgh")
    content = (session_dir / "contexts" / filename).read_text(encoding="utf-8")
    assert "## 무엇을 왜" in content
    assert "## 주요 결정" in content
    assert "## 미완료" in content
    assert "## 다음 세션 지침" in content


def test_write_appends_to_same_hour(tmp_path):
    session_dir = tmp_path / "s1"
    (session_dir / "contexts").mkdir(parents=True)
    hw.write_context_file(str(session_dir), "auth", "en", _make_result("First entry."), "sess1")
    hw.write_context_file(str(session_dir), "auth", "en", _make_result("Second entry."), "sess1")
    files = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    assert len(files) == 1  # both entries in one file
    content = files[0].read_text(encoding="utf-8")
    assert "First entry." in content
    assert "Second entry." in content


def test_write_empty_decisions_shows_none(tmp_path):
    session_dir = tmp_path / "s1"
    (session_dir / "contexts").mkdir(parents=True)
    result = _make_result(decisions=[], incomplete=[])
    hw.write_context_file(str(session_dir), "auth", "en", result, "sess1")
    files = list((session_dir / "contexts").glob("CONTEXT-*.md"))
    content = files[0].read_text(encoding="utf-8")
    assert "- None" in content


def test_write_returns_filename(tmp_path):
    session_dir = tmp_path / "s1"
    (session_dir / "contexts").mkdir(parents=True)
    filename = hw.write_context_file(str(session_dir), "jwt-auth", "en", _make_result(), "s1")
    assert filename.startswith("CONTEXT-")
    assert filename.endswith(".md")


# ── update_index (new signature) ─────────────────────────────────────

def test_update_index_filename_format(tmp_path):
    session_dir = tmp_path / "sess"
    hw.create_index(str(session_dir), "test-session", str(tmp_path))
    index_data = hw.read_index(session_dir)
    hw.update_index(
        session_dir, index_data,
        last_uuid="uuid1",
        new_head="sha1",
        filename="CONTEXT-20260419-1400-jwt-auth.md",
        one_liner="Added JWT auth",
    )
    content = (session_dir / "INDEX.md").read_text(encoding="utf-8")
    assert "[CONTEXT-20260419-1400-jwt-auth.md]" in content
    assert "Added JWT auth" in content
    assert "[0001]" not in content
