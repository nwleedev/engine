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


# --- _extract_section ---

def test_extract_section_core_rules():
    content = (
        "---\ndomain: test\n---\n"
        "## Core Rules\n\n- [ ] Rule one\n- [ ] Rule two\n\n"
        "## Pattern Examples\n\nsome examples"
    )
    result = gh._extract_section(content, "## Core Rules")
    assert "Rule one" in result
    assert "Pattern Examples" not in result


def test_extract_section_anti_pattern_gate():
    content = (
        "## Anti-Pattern Gate\n\n```\nUsing X? → Fix Y\n```\n\n"
        "## Something Else\n\nother content"
    )
    result = gh._extract_section(content, "## Anti-Pattern Gate")
    assert "Using X?" in result
    assert "Something Else" not in result


def test_extract_section_missing_returns_empty():
    content = "## Core Rules\n\n- [ ] Rule one\n"
    result = gh._extract_section(content, "## Anti-Pattern Gate")
    assert result == ""


# --- generate_skill_file ---

def test_generate_skill_file_creates_skill_md(tmp_path):
    harness_content = (
        "---\ndomain: market-research\ndomain_type: document\n"
        "keywords: [market, TAM]\n---\n"
        "## Core Rules\n\n- [ ] Every claim backed by source\n\n"
        "## Anti-Pattern Gate\n\n```\nUsing 'large'? → Add TAM figure\n```\n"
    )
    path = gh.generate_skill_file("market-research", harness_content, str(tmp_path))
    skill_path = tmp_path / ".claude" / "skills" / "market-research-harness" / "SKILL.md"
    assert skill_path.exists()
    assert path == str(skill_path)


def test_generate_skill_file_embeds_core_rules(tmp_path):
    harness_content = (
        "## Core Rules\n\n- [ ] Every claim backed by source\n\n"
        "## Anti-Pattern Gate\n\n```\nUsing 'large'? → Add TAM figure\n```\n"
    )
    gh.generate_skill_file("market-research", harness_content, str(tmp_path))
    skill_path = tmp_path / ".claude" / "skills" / "market-research-harness" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    assert "Every claim backed by source" in content
    assert "Using 'large'?" in content


def test_generate_skill_file_frontmatter_name(tmp_path):
    harness_content = "## Core Rules\n\n- [ ] Rule\n\n## Anti-Pattern Gate\n\n```\nQ? → A\n```\n"
    gh.generate_skill_file("prd-writing", harness_content, str(tmp_path))
    skill_path = tmp_path / ".claude" / "skills" / "prd-writing-harness" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    assert "name: prd-writing-harness" in content
    assert "description:" in content


def test_generate_skill_file_overwrites_existing(tmp_path):
    harness_v1 = (
        "## Core Rules\n\n- [ ] Rule v1\n\n"
        "## Anti-Pattern Gate\n\n```\nQ? → A\n```\n"
    )
    harness_v2 = (
        "## Core Rules\n\n- [ ] Rule v2\n\n"
        "## Anti-Pattern Gate\n\n```\nQ? → A\n```\n"
    )
    gh.generate_skill_file("market-research", harness_v1, str(tmp_path))
    gh.generate_skill_file("market-research", harness_v2, str(tmp_path))
    skill_path = tmp_path / ".claude" / "skills" / "market-research-harness" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    assert "Rule v2" in content
    assert "Rule v1" not in content


# --- non-dev templates ---

@pytest.mark.parametrize("domain", [
    "prd-writing", "pitch-deck", "technical-writing",
    "data-analysis", "okr-planning", "risk-assessment",
])
def test_get_template_nondev_exists(domain):
    content = gh.get_template(domain, str(PLUGIN_ROOT))
    assert "## Core Rules" in content
    assert "## Anti-Pattern Gate" in content
    assert "domain_type: document" in content


def test_market_research_template_has_domain_type():
    content = gh.get_template("market-research", str(PLUGIN_ROOT))
    assert "domain_type: document" in content
