import sys
from pathlib import Path
from unittest import mock
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
PLUGIN_ROOT = Path(__file__).parent.parent.parent / "plugins/harness-engineer"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_harness as gh


# --- get_template ---

def test_get_template_react_exists():
    content = gh.get_template("react-frontend", str(PLUGIN_ROOT))
    assert "react-frontend" in content.lower() or "React" in content


def test_get_template_unknown_domain():
    content = gh.get_template("unknown-domain", str(PLUGIN_ROOT))
    assert "unknown-domain" in content  # generic template fallback


# --- build_harness_frontmatter ---

def test_build_harness_frontmatter_ko():
    result = gh.build_harness_frontmatter("react-frontend", "ko")
    assert "language: ko" in result
    assert "domain: react-frontend" in result


def test_build_harness_frontmatter_includes_today():
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    result = gh.build_harness_frontmatter("react-frontend", "en")
    assert today in result


# --- generate_harness_file ---

def test_generate_harness_file_replaces_frontmatter_language():
    content = gh.generate_harness_file("react-frontend", "/tmp/proj", "ko", str(PLUGIN_ROOT))
    assert "language: ko" in content


def test_generate_harness_file_replaces_frontmatter_date():
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    content = gh.generate_harness_file("react-frontend", "/tmp/proj", "en", str(PLUGIN_ROOT))
    assert f"updated: {today}" in content


# --- _parse_frontmatter_list (generic) ---

def test_parse_frontmatter_list_keywords():
    template = "---\ndomain: react-frontend\nkeywords: [tsx, jsx]\n---\n# body"
    result = gh._parse_frontmatter_list(template, "keywords")
    assert result == ["tsx", "jsx"]


def test_parse_frontmatter_list_file_patterns():
    template = '---\ndomain: react-frontend\nfile_patterns: ["*.tsx", "src/**"]\n---\n# body'
    result = gh._parse_frontmatter_list(template, "file_patterns")
    assert "*.tsx" in result
    assert "src/**" in result


def test_parse_frontmatter_list_missing_field():
    template = "---\ndomain: react-frontend\n---\n# body"
    result = gh._parse_frontmatter_list(template, "file_patterns")
    assert result == []


def test_parse_frontmatter_list_no_frontmatter():
    result = gh._parse_frontmatter_list("# No frontmatter", "keywords")
    assert result == []


# --- build_harness_frontmatter with file_patterns ---

def test_build_harness_frontmatter_with_file_patterns():
    result = gh.build_harness_frontmatter(
        "react-frontend", "ko",
        keywords=["tsx", "component"],
        file_patterns=["*.tsx", "src/**"],
    )
    assert 'file_patterns: ["*.tsx", "src/**"]' in result


def test_build_harness_frontmatter_no_file_patterns():
    result = gh.build_harness_frontmatter("react-frontend", "en")
    assert "file_patterns" not in result


def test_build_harness_frontmatter_empty_file_patterns():
    result = gh.build_harness_frontmatter(
        "react-frontend", "en",
        keywords=[], file_patterns=[]
    )
    assert "keywords: []" in result
    assert "file_patterns: []" in result


# --- generate_harness_file preserves file_patterns ---

def test_generate_harness_file_preserves_file_patterns():
    content = gh.generate_harness_file("react-frontend", "/tmp/proj", "ko", str(PLUGIN_ROOT))
    assert "file_patterns" in content
    assert "*.tsx" in content


# --- domain_type in frontmatter ---

def test_build_harness_frontmatter_document_type():
    result = gh.build_harness_frontmatter(
        "market-research", "auto", domain_type="document"
    )
    assert "domain_type: document" in result


def test_build_harness_frontmatter_code_type_is_default():
    result = gh.build_harness_frontmatter("react-frontend", "en")
    # default: domain_type: code or omitted — either is acceptable
    # but if included it must be "code"
    if "domain_type" in result:
        assert "domain_type: code" in result


def test_build_harness_frontmatter_document_empty_file_patterns():
    result = gh.build_harness_frontmatter(
        "market-research", "auto",
        keywords=["market", "TAM"],
        file_patterns=[],
        domain_type="document",
    )
    assert "file_patterns: []" in result
    assert "domain_type: document" in result
