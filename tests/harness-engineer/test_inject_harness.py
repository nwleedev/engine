import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import inject_harness as ih


REACT_HARNESS = (FIXTURES_DIR / "sample_harness_react.md").read_text(encoding="utf-8")
MARKET_HARNESS = (FIXTURES_DIR / "sample_harness_market.md").read_text(encoding="utf-8")


# --- extract_core_rules ---

def test_extract_core_rules_returns_checklist_section():
    result = ih.extract_core_rules(REACT_HARNESS)
    assert "Core Rules" in result
    assert "any" in result


def test_extract_core_rules_does_not_include_pattern_section():
    result = ih.extract_core_rules(REACT_HARNESS)
    assert "Pattern Examples" not in result


def test_extract_core_rules_max_15_lines():
    result = ih.extract_core_rules(REACT_HARNESS)
    assert len(result.splitlines()) <= 15


def test_extract_core_rules_no_section_returns_empty():
    result = ih.extract_core_rules("# No sections here\nJust content.")
    assert result == ""


def test_extract_core_rules_max_15_lines_at_boundary():
    rules_lines = [f"- [ ] Rule {i}" for i in range(20)]
    content = "## Core Rules\n\n" + "\n".join(rules_lines) + "\n\n## Next Section\n"
    result = ih.extract_core_rules(content)
    assert len(result.splitlines()) <= 15


def test_extract_core_rules_english_header():
    content = "---\ndomain: test\n---\n\n## Core Rules\n\n- [ ] No any types\n- [ ] Use proper types\n\n## Patterns\n\nSome pattern here."
    result = ih.extract_core_rules(content)
    assert "Core Rules" in result
    assert "No any types" in result
    assert "Patterns" not in result


# --- build_user_prompt_context ---

def test_build_user_prompt_context_single_file():
    files = [{"domain": "react-frontend", "content": REACT_HARNESS}]
    result = ih.build_user_prompt_context(files)
    assert "React Frontend Harness" in result
    assert "Core Rules" in result


def test_build_user_prompt_context_multiple_files():
    files = [
        {"domain": "react-frontend", "content": REACT_HARNESS},
        {"domain": "market-research", "content": MARKET_HARNESS},
    ]
    result = ih.build_user_prompt_context(files)
    assert "React Frontend Harness" in result
    assert "Market Research Harness" in result
    assert "\n\n---\n\n" in result


def test_build_user_prompt_context_empty():
    assert ih.build_user_prompt_context([]) == ""


# --- build_pre_tool_context ---

def test_build_pre_tool_context_includes_domain_name():
    f = {"domain": "react-frontend", "content": REACT_HARNESS}
    result = ih.build_pre_tool_context(f)
    assert "react-frontend" in result


def test_build_pre_tool_context_contains_checklist():
    f = {"domain": "react-frontend", "content": REACT_HARNESS}
    result = ih.build_pre_tool_context(f)
    assert "any" in result


def test_build_pre_tool_context_is_short():
    f = {"domain": "react-frontend", "content": REACT_HARNESS}
    result = ih.build_pre_tool_context(f)
    assert len(result.splitlines()) <= 20


def test_build_pre_tool_context_no_rules_returns_empty():
    f = {"domain": "react-frontend", "content": "# No rules here\nJust content."}
    result = ih.build_pre_tool_context(f)
    assert result == ""
