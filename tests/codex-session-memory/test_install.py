import importlib.util
from pathlib import Path

import pytest


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex" / "session-memory"
SCRIPTS = PLUGIN / "scripts"


def load_agents_rules():
    spec = importlib.util.spec_from_file_location("agents_rules", SCRIPTS / "agents_rules.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_detects_missing_when_agents_file_absent(tmp_path):
    rules = load_agents_rules()
    report = rules.check_agents_rules(tmp_path)

    assert report.status == "not found"
    assert report.missing
    assert "AGENTS.md" in report.patch


def test_detects_installed_rules(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(rules.REQUIRED_BLOCK, encoding="utf-8")

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "installed"
    assert report.missing == ()
    assert report.patch == ""


def test_default_required_block_is_english_and_ko_block_is_opt_in():
    rules = load_agents_rules()

    assert rules.REQUIRED_BLOCK == rules.REQUIRED_BLOCK_EN
    assert "context compaction" in rules.REQUIRED_BLOCK_EN
    assert "Context compaction" not in rules.REQUIRED_BLOCK_EN
    assert "컨텍스트 압축" in rules.REQUIRED_BLOCK_KO
    assert rules.required_block("en") == rules.REQUIRED_BLOCK_EN
    assert rules.required_block("ko") == rules.REQUIRED_BLOCK_KO
    assert rules.required_block(None) == rules.REQUIRED_BLOCK_EN


def test_detects_partial_rules(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "$session-memory:checkpoint\n"
        "$session-memory:status\n",
        encoding="utf-8",
    )

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "partial"
    assert "$session-memory:resume" in "\n".join(report.missing)
    assert "## Codex Session Memory" in report.patch


def test_detects_missing_markers_from_incomplete_section(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "## Codex Session Memory\n\n"
        "- `$session-memory:checkpoint`\n"
        "- `$session-memory:status`\n\n"
        "## Other Rules\n\n"
        "$session-memory:resume\n"
        "CODEX_THREAD_ID\n"
        ".codex/\n"
        "컨텍스트 압축\n"
        "첫 행동\n",
        encoding="utf-8",
    )

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "partial"
    assert "$session-memory:resume" in report.missing
    assert "CODEX_THREAD_ID" in report.missing


def test_does_not_install_when_markers_are_scattered_outside_section(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "# Project Rules\n\n"
        "$session-memory:checkpoint\n"
        "$session-memory:resume\n"
        "$session-memory:status\n"
        "CODEX_THREAD_ID\n"
        ".codex/\n"
        "컨텍스트 압축\n"
        "첫 행동\n",
        encoding="utf-8",
    )

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "partial"
    assert report.missing == (rules.SECTION_HEADING,)
    assert report.patch


def test_no_section_partial_reports_only_actual_missing_markers(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "# Project Rules\n\n"
        "$session-memory:checkpoint\n"
        "$session-memory:status\n",
        encoding="utf-8",
    )

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "partial"
    assert "$session-memory:checkpoint" not in report.missing
    assert "$session-memory:status" not in report.missing
    assert "$session-memory:resume" in report.missing
    assert "CODEX_THREAD_ID" in report.missing


def test_non_installed_reports_have_missing_markers(tmp_path):
    rules = load_agents_rules()
    reports = []

    reports.append(rules.check_agents_rules(tmp_path / "absent"))

    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    (missing_root / "AGENTS.md").write_text("# Project Rules\n", encoding="utf-8")
    reports.append(rules.check_agents_rules(missing_root))

    partial_root = tmp_path / "partial"
    partial_root.mkdir()
    (partial_root / "AGENTS.md").write_text(
        "## Codex Session Memory\n"
        "$session-memory:checkpoint\n",
        encoding="utf-8",
    )
    reports.append(rules.check_agents_rules(partial_root))

    for report in reports:
        assert report.status != "installed"
        assert report.missing


def test_missing_markers_are_immutable(tmp_path):
    rules = load_agents_rules()
    report = rules.check_agents_rules(tmp_path)

    with pytest.raises(AttributeError):
        report.missing.append("another-marker")


def load_install_skill():
    skill = PLUGIN / "skills" / "install" / "install.py"
    spec = importlib.util.spec_from_file_location("install_skill", skill)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def configure_install_root(install, monkeypatch, root):
    monkeypatch.setattr(install.csm_project_root, "find_project_root", lambda cwd: str(root))
    monkeypatch.setattr(install.os, "getcwd", lambda: str(root))


def test_install_skill_instructions_require_user_visible_stdout_relay():
    skill_text = (PLUGIN / "skills" / "install" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "always relay the script stdout to the user" in skill_text
    assert "include the full recommended block from stdout" in skill_text
    assert "exit code 1" in skill_text
    assert "Do not edit AGENTS.md unless the user explicitly asks" in skill_text


def test_install_skill_prints_missing_patch_without_modifying_agents(
    tmp_path, monkeypatch, capsys
):
    install = load_install_skill()
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Project Rules\n", encoding="utf-8")
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main([]) == 1

    output = capsys.readouterr().out
    assert "status: missing" in output
    assert "Add this block:" in output
    assert "context compaction" in output
    assert "Context compaction" not in output
    assert agents.read_text(encoding="utf-8") == "# Project Rules\n"


def test_install_skill_prints_korean_patch_when_ko_arg_is_passed(
    tmp_path, monkeypatch, capsys
):
    install = load_install_skill()
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Project Rules\n", encoding="utf-8")
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main(["ko"]) == 1

    output = capsys.readouterr().out
    assert "status: missing" in output
    assert "Add this block:" in output
    assert "컨텍스트 압축" in output


def test_install_skill_prints_english_patch_when_en_arg_is_passed(
    tmp_path, monkeypatch, capsys
):
    install = load_install_skill()
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Project Rules\n", encoding="utf-8")
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main(["en"]) == 1

    output = capsys.readouterr().out
    assert "status: missing" in output
    assert "Add this block:" in output
    assert "context compaction" in output
    assert "Context compaction" not in output


def test_install_skill_returns_zero_for_installed_rules(tmp_path, monkeypatch, capsys):
    install = load_install_skill()
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(rules.REQUIRED_BLOCK, encoding="utf-8")
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main([]) == 0

    output = capsys.readouterr().out
    assert "status: installed" in output
    assert "missing markers:" not in output
    assert "Add this block:" not in output


def test_install_skill_returns_one_for_not_found_rules(tmp_path, monkeypatch, capsys):
    install = load_install_skill()
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main([]) == 1

    output = capsys.readouterr().out
    assert "status: not found" in output
    assert "missing markers:" in output
    assert "Add this block:" in output


def test_install_skill_returns_one_for_partial_rules(tmp_path, monkeypatch, capsys):
    install = load_install_skill()
    (tmp_path / "AGENTS.md").write_text(
        "## Codex Session Memory\n\n"
        "- `$session-memory:checkpoint`\n",
        encoding="utf-8",
    )
    configure_install_root(install, monkeypatch, tmp_path)

    assert install.main([]) == 1

    output = capsys.readouterr().out
    assert "status: partial" in output
    assert "missing markers:" in output
    assert "- $session-memory:resume" in output
    assert "Add this block:" in output


def test_install_skill_rejects_unexpected_args(capsys):
    install = load_install_skill()

    assert install.main(["--help"]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: install.py [en|ko]" in captured.err
