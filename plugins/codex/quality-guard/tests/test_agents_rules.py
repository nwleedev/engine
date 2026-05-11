import importlib.util
from pathlib import Path


def load_agents_rules():
    path = Path(__file__).resolve().parents[1] / "scripts" / "agents_rules.py"
    spec = importlib.util.spec_from_file_location("test_cqg_agents_rules", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys

    sys.modules["test_cqg_agents_rules"] = module
    spec.loader.exec_module(module)
    return module


def test_not_found_reports_recommended_block(tmp_path):
    rules = load_agents_rules()
    report = rules.check_agents_rules(tmp_path)
    assert report.status == "not found"
    assert "codex-quality-guard:retrospect" in report.guidance
    assert "Superficial risk" in report.missing


def test_missing_when_agents_exists_without_quality_guard(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text("# AGENTS.md\n\nGeneral rules.\n", encoding="utf-8")
    report = rules.check_agents_rules(tmp_path)
    assert report.status == "missing"
    assert "codex-quality-guard:retrospect" in report.missing
    assert "Add this block:" in report.guidance


def test_installed_when_section_has_required_markers(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(rules.RECOMMENDED_BLOCK, encoding="utf-8")
    report = rules.check_agents_rules(tmp_path)
    assert report.status == "installed"
    assert report.missing == ()
    assert report.guidance == ""


def test_partial_when_section_is_incomplete(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "## Codex Quality Guard\n\n"
        "- Run `codex-quality-guard:retrospect` before finishing.\n",
        encoding="utf-8",
    )
    report = rules.check_agents_rules(tmp_path)
    assert report.status == "partial"
    assert "unknown" in report.missing
    assert "/review" in report.missing


def test_korean_guidance_contains_korean_block(tmp_path):
    rules = load_agents_rules()
    report = rules.check_agents_rules(tmp_path, locale="ko")
    assert "각 작업 턴을 마치기 전에" in report.guidance
    assert "codex-quality-guard:retrospect" in report.guidance


def test_korean_block_is_installed(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(rules.RECOMMENDED_BLOCK_KO, encoding="utf-8")
    report = rules.check_agents_rules(tmp_path)
    assert report.status == "installed"
    assert report.missing == ()
