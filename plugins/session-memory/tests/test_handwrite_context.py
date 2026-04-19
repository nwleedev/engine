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
    assert "ko" in prompt
    assert "test conversation" in prompt


def test_build_prompt_includes_truncation_note():
    prompt = hw.build_prompt("text", True, "en")
    assert "omitted" in prompt.lower() or "earlier" in prompt.lower()


def test_build_prompt_no_note_when_not_truncated():
    prompt = hw.build_prompt("text", False, "en")
    assert "omitted" not in prompt.lower()
