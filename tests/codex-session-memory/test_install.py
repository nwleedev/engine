import importlib.util
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
SCRIPTS = PLUGIN / "scripts"


def load_agents_rules():
    spec = importlib.util.spec_from_file_location("agents_rules", SCRIPTS / "agents_rules.py")
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
    assert report.missing == []
    assert report.patch == ""


def test_detects_partial_rules(tmp_path):
    rules = load_agents_rules()
    (tmp_path / "AGENTS.md").write_text(
        "$codex-session-memory:checkpoint\n"
        "$codex-session-memory:status\n",
        encoding="utf-8",
    )

    report = rules.check_agents_rules(tmp_path)

    assert report.status == "partial"
    assert "$codex-session-memory:resume" in "\n".join(report.missing)
    assert "## Codex Session Memory" in report.patch
