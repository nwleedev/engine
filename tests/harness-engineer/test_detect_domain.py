# tests/harness-engineer/test_detect_domain.py
import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import detect_domain as dd


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
        "---\ndomain: react-frontend\nkeywords: [tsx, component]\n---\n# Content",
        encoding="utf-8"
    )
    result = dd.load_harness_files(tmp_path)
    assert len(result) == 1
    assert result[0]["domain"] == "react-frontend"
    assert "tsx" in result[0]["keywords"]


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


# --- detect_domain_from_file_path ---

def test_detect_domain_from_tsx_path():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("src/components/Button.tsx", files)
    assert result is not None
    assert result["domain"] == "react-frontend"


def test_detect_domain_from_jsx_path():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("components/Card.jsx", files)
    assert result is not None


def test_detect_domain_from_python_path():
    files = [{"domain": "python-backend", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("app/api/users.py", files)
    assert result is not None
    assert result["domain"] == "python-backend"


def test_detect_domain_from_unrecognized_path():
    files = [{"domain": "react-frontend", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("README.md", files)
    assert result is None


def test_detect_domain_from_research_path():
    files = [{"domain": "market-research", "keywords": [], "content": "x"}]
    result = dd.detect_domain_from_file_path("docs/research/competitor.md", files)
    assert result is not None
    assert result["domain"] == "market-research"
