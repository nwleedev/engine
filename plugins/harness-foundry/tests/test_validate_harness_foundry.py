import subprocess
import json
import shutil
from pathlib import Path


ROOT = Path("plugins/harness-foundry")
VALIDATOR = ROOT / "scripts" / "validate_harness_foundry.py"


def run_validator(path: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        check=False,
        text=True,
        capture_output=True,
    )


def copy_plugin(tmp_path: Path) -> Path:
    target = tmp_path / "harness-foundry"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns("__pycache__"))
    return target


def test_validate_harness_foundry_script_passes():
    result = run_validator()
    assert result.returncode == 0
    assert "harness-foundry validation passed" in result.stdout


def test_validator_rejects_manifest_components_outside_v1(tmp_path):
    plugin = copy_plugin(tmp_path)
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["mcpServers"] = {}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "non-v1 keys" in result.stdout


def test_validator_rejects_missing_short_description(tmp_path):
    plugin = copy_plugin(tmp_path)
    skill_path = plugin / "skills" / "diagnose-project" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(
        text.replace("  short-description: Diagnose domain harness candidates\n", ""),
        encoding="utf-8",
    )

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing metadata.short-description" in result.stdout


def test_validator_rejects_missing_readme_boundary(tmp_path):
    plugin = copy_plugin(tmp_path)
    readme_path = plugin / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    readme_path.write_text(
        text.replace("- It does not bulk-install public awesome repositories.\n", ""),
        encoding="utf-8",
    )

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "README.md missing boundary pattern" in result.stdout
