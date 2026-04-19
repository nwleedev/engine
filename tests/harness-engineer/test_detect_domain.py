# tests/harness-engineer/test_detect_domain.py
import importlib.util
import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

_spec = importlib.util.spec_from_file_location("harness_engineer.detect_domain", SCRIPTS_DIR / "detect_domain.py")
assert _spec is not None and _spec.loader is not None
dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dd)


# --- parse_harness_frontmatter ---

def test_parse_frontmatter_basic():
    content = "---\ndomain: react-frontend\nlanguage: auto\n---\n# Body"
    result = dd.parse_harness_frontmatter(content)
    assert result["domain"] == "react-frontend"
    assert result["language"] == "auto"


def test_parse_frontmatter_keywords_list():
    content = "---\ndomain: react-frontend\nkeywords: [컴포넌트, component, tsx]\n---"
    result = dd.parse_harness_frontmatter(content)
    assert "컴포넌트" in result["keywords"]
    assert "tsx" in result["keywords"]


def test_parse_frontmatter_no_frontmatter():
    content = "# Just a header\nNo frontmatter here."
    result = dd.parse_harness_frontmatter(content)
    assert result == {}


def test_parse_frontmatter_empty():
    assert dd.parse_harness_frontmatter("") == {}


# --- load_harness_files ---

def test_load_harness_files(tmp_path):
    react_file = tmp_path / "react-frontend.md"
    react_file.write_text(
        '---\ndomain: react-frontend\nkeywords: [tsx, component]\nfile_patterns: ["*.tsx", "src/**"]\n---\n# Content',
        encoding="utf-8"
    )
    result = dd.load_harness_files(tmp_path)
    assert len(result) == 1
    assert result[0]["domain"] == "react-frontend"
    assert "tsx" in result[0]["keywords"]
    assert "*.tsx" in result[0]["file_patterns"]
    assert "src/**" in result[0]["file_patterns"]


def test_load_harness_files_skips_violations_log(tmp_path):
    (tmp_path / "violations.log").write_text("some log", encoding="utf-8")
    result = dd.load_harness_files(tmp_path)
    assert result == []


def test_load_harness_files_empty_dir(tmp_path):
    assert dd.load_harness_files(tmp_path) == []


# --- detect_domains_from_prompt ---

def test_detect_domains_from_prompt_korean_keyword():
    files = [{"domain": "react-frontend", "keywords": ["컴포넌트", "tsx"], "content": "x"}]
    result = dd.detect_domains_from_prompt("Button 컴포넌트에 로딩 추가해줘", files)
    assert len(result) == 1
    assert result[0]["domain"] == "react-frontend"


def test_detect_domains_from_prompt_english_keyword():
    files = [{"domain": "react-frontend", "keywords": ["component", "tsx"], "content": "x"}]
    result = dd.detect_domains_from_prompt("Add loading to Button component", files)
    assert len(result) == 1


def test_detect_domains_from_prompt_no_match():
    files = [{"domain": "react-frontend", "keywords": ["컴포넌트", "tsx"], "content": "x"}]
    result = dd.detect_domains_from_prompt("데이터베이스 스키마 설계해줘", files)
    assert result == []


def test_detect_domains_from_prompt_max_three():
    files = [
        {"domain": f"domain-{i}", "keywords": ["공통키워드"], "content": "x"}
        for i in range(5)
    ]
    result = dd.detect_domains_from_prompt("공통키워드 관련 작업", files)
    assert len(result) <= 3


# --- _matches_pattern ---

def test_matches_extension_pattern():
    assert dd._matches_pattern("Button.tsx", "*.tsx") is True


def test_matches_extension_pattern_in_path():
    assert dd._matches_pattern("src/components/Button.tsx", "*.tsx") is True


def test_matches_full_path_double_star():
    assert dd._matches_pattern("src/components/Button.tsx", "src/components/**") is True


def test_matches_double_star_prefix():
    assert dd._matches_pattern("app/dashboard/page.tsx", "app/**") is True


def test_matches_double_star_suffix():
    assert dd._matches_pattern("apps/web/src/Button.tsx", "**/*.tsx") is True


def test_no_match_wrong_extension():
    assert dd._matches_pattern("Button.py", "*.tsx") is False


def test_no_match_wrong_prefix():
    assert dd._matches_pattern("pages/index.tsx", "app/**") is False


def test_matches_exact_filename():
    assert dd._matches_pattern("src/config.py", "*.py") is True


# --- detect_domain_from_file_path (new: reads from file_patterns) ---

def test_detect_domain_uses_file_patterns():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x",
              "file_patterns": ["*.tsx", "src/components/**"]}]
    result = dd.detect_domain_from_file_path("src/components/Button.tsx", files)
    assert result is not None
    assert result["domain"] == "react-frontend"


def test_detect_domain_no_file_patterns_returns_none():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x",
              "file_patterns": []}]
    result = dd.detect_domain_from_file_path("Button.tsx", files)
    assert result is None


def test_detect_domain_multiple_harness_files_first_match_wins():
    files = [
        {"domain": "frontend", "keywords": [], "content": "x",
         "file_patterns": ["*.tsx"]},
        {"domain": "backend", "keywords": [], "content": "x",
         "file_patterns": ["*.tsx", "*.py"]},
    ]
    result = dd.detect_domain_from_file_path("Button.tsx", files)
    assert result["domain"] == "frontend"


def test_detect_domain_unrecognized_path_returns_none():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x",
              "file_patterns": ["*.tsx"]}]
    result = dd.detect_domain_from_file_path("README.md", files)
    assert result is None


def test_matches_double_star_alone():
    assert dd._matches_pattern("any/file.tsx", "**") is True


def test_matches_double_star_suffix_flat_file():
    # flat file (no directory) against **/*.tsx
    assert dd._matches_pattern("Button.tsx", "**/*.tsx") is True


def test_detect_domain_missing_file_patterns_key():
    # harness dict with no file_patterns key at all (not just empty list)
    files = [{"domain": "test", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("Button.tsx", files)
    assert result is None
