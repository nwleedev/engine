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


# --- build_anti_frame_bias_context ---

def test_build_anti_frame_bias_context_is_xml_block():
    result = ir.build_anti_frame_bias_context()
    assert result.startswith("<cognitive-debiasing>")
    assert result.strip().endswith("</cognitive-debiasing>")

def test_build_anti_frame_bias_context_contains_four_steps():
    result = ir.build_anti_frame_bias_context()
    assert "SUSPEND" in result
    assert "ENUMERATE" in result
    assert "MULTI-AXIS" in result
    assert "VERIFY" in result

def test_build_anti_frame_bias_context_has_four_numbered_steps():
    result = ir.build_anti_frame_bias_context()
    for i in range(1, 5):
        assert f"{i}." in result


# --- detect_design_keyword ---

def test_detect_design_keyword_korean_design():
    assert ir.detect_design_keyword("어떻게 설계할까요?") is True

def test_detect_design_keyword_korean_method():
    assert ir.detect_design_keyword("방법을 알려주세요") is True

def test_detect_design_keyword_korean_approach():
    assert ir.detect_design_keyword("접근법이 뭔가요") is True

def test_detect_design_keyword_korean_implement():
    assert ir.detect_design_keyword("구현 방식을 논의합시다") is True

def test_detect_design_keyword_korean_how():
    assert ir.detect_design_keyword("어떻게 하면 될까요") is True

def test_detect_design_keyword_korean_strategy():
    assert ir.detect_design_keyword("전략을 세워봅시다") is True

def test_detect_design_keyword_english_design():
    assert ir.detect_design_keyword("how should we design this?") is True

def test_detect_design_keyword_english_approach():
    assert ir.detect_design_keyword("what approach should we take?") is True

def test_detect_design_keyword_english_implement():
    assert ir.detect_design_keyword("let's implement the feature") is True

def test_detect_design_keyword_english_architect():
    assert ir.detect_design_keyword("architect the new system") is True

def test_detect_design_keyword_english_strategy():
    assert ir.detect_design_keyword("the strategy should be reconsidered") is True

def test_detect_design_keyword_no_match():
    assert ir.detect_design_keyword("what is the capital of France?") is False

def test_detect_design_keyword_empty():
    assert ir.detect_design_keyword("") is False


# --- build_criterion_guided_evaluation ---

def test_build_criterion_guided_evaluation_is_xml_block():
    result = ir.build_criterion_guided_evaluation()
    assert result.startswith("<cognitive-debiasing>")
    assert result.strip().endswith("</cognitive-debiasing>")

def test_build_criterion_guided_evaluation_has_six_steps():
    result = ir.build_criterion_guided_evaluation()
    for i in range(1, 7):
        assert f"{i}." in result

def test_build_criterion_guided_evaluation_contains_evaluate_step():
    result = ir.build_criterion_guided_evaluation()
    assert "EVALUATE" in result
    assert "PROHIBITED" in result
    assert "fewer changes required" in result
    assert "faster to implement" in result
    assert "more familiar" in result

def test_build_criterion_guided_evaluation_contains_declare_step():
    result = ir.build_criterion_guided_evaluation()
    assert "DECLARE" in result
    assert "Root cause" in result
    assert "hardcoding" in result
    assert "special-casing" in result
    assert "exception hiding" in result

def test_build_criterion_guided_evaluation_contains_required_criteria():
    result = ir.build_criterion_guided_evaluation()
    assert "Correctness" in result
    assert "Standard compliance" in result
    assert "Maintainability" in result

def test_build_criterion_guided_evaluation_preserves_original_four_steps():
    result = ir.build_criterion_guided_evaluation()
    assert "SUSPEND" in result
    assert "ENUMERATE" in result
    assert "MULTI-AXIS" in result
    assert "VERIFY" in result
