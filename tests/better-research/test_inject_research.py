import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/better-research/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import inject_research as ir


# --- load_skill_md ---

def test_load_skill_md_returns_content(tmp_path):
    skill_dir = tmp_path / "skills" / "research-protocol"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Research Protocol\n\n## Step 1", encoding="utf-8")
    result = ir.load_skill_md(str(tmp_path))
    assert "Research Protocol" in result


def test_load_skill_md_missing_file_returns_empty(tmp_path):
    result = ir.load_skill_md(str(tmp_path))
    assert result == ""


def test_load_skill_md_missing_directory_returns_empty(tmp_path):
    result = ir.load_skill_md(str(tmp_path / "nonexistent"))
    assert result == ""


# --- build_perspective_context ---

def test_build_perspective_context_includes_all_perspectives():
    result = ir.build_perspective_context("validity,root_cause_solution,cross_check")
    assert "validity" in result
    assert "root_cause_solution" in result
    assert "cross_check" in result


def test_build_perspective_context_trims_whitespace():
    result = ir.build_perspective_context("  validity , cross_check  ")
    assert "validity" in result
    assert "cross_check" in result


def test_build_perspective_context_empty_string_returns_empty():
    assert ir.build_perspective_context("") == ""


def test_build_perspective_context_whitespace_only_returns_empty():
    assert ir.build_perspective_context("   ") == ""


# --- assemble_context ---

def test_assemble_context_joins_with_separator():
    result = ir.assemble_context(["part1", "part2"])
    assert "part1" in result
    assert "part2" in result
    assert "\n\n---\n\n" in result


def test_assemble_context_skips_empty_parts():
    result = ir.assemble_context(["part1", "", "part2"])
    assert result == "part1\n\n---\n\npart2"


def test_assemble_context_single_part_no_separator():
    result = ir.assemble_context(["only"])
    assert result == "only"
    assert "---" not in result


def test_assemble_context_all_empty_returns_empty():
    assert ir.assemble_context(["", "", ""]) == ""


# --- build_core_debiasing ---

def test_build_core_debiasing_is_xml_block():
    result = ir.build_core_debiasing()
    assert result.startswith("<cognitive-debiasing>")
    assert result.strip().endswith("</cognitive-debiasing>")


def test_build_core_debiasing_has_seven_steps():
    import re
    result = ir.build_core_debiasing()
    steps = re.findall(r'^\d+\.', result, re.MULTILINE)
    assert len(steps) == 7


def test_build_core_debiasing_contains_all_step_names():
    result = ir.build_core_debiasing()
    for name in ("SUSPEND", "ENUMERATE", "MULTI-AXIS", "VERIFY", "COUNTER", "EVALUATE", "DECLARE"):
        assert name in result


def test_build_core_debiasing_contains_counter_step():
    result = ir.build_core_debiasing()
    assert "COUNTER" in result
    assert "wrong" in result.lower()


def test_build_core_debiasing_contains_prohibited_criteria():
    result = ir.build_core_debiasing()
    assert "Prohibited" in result
    assert "faster" in result
    assert "familiar" in result


def test_build_core_debiasing_english_only():
    result = ir.build_core_debiasing()
    assert not any('가' <= c <= '힣' for c in result)
