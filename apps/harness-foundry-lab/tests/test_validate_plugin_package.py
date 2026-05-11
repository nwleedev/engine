import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex" / "harness-foundry"
VALIDATOR = REPO_ROOT / "apps" / "harness-foundry-lab" / "scripts" / "validate_plugin_package.py"
SKILLS = (
    "diagnose-project",
    "design-domain-harness",
    "update-registry",
    "scaffold-domain-harness",
    "audit-domain-harness",
)
REFERENCE_FILES = (
    "domain-harness-template.md",
    "registry-template.md",
    "evaluation-template.md",
    "risk-checklist.md",
)


def read_plugin_file(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


def load_validator_module():
    spec = importlib.util.spec_from_file_location("_test_validate_plugin_package", VALIDATOR)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_validator(*args: Path | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VALIDATOR), *[str(arg) for arg in args]],
        check=False,
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
    )


def copy_plugin(tmp_path: Path) -> Path:
    target = tmp_path / "harness-foundry"
    shutil.copytree(
        PLUGIN_ROOT,
        target,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    return target


def test_parse_args_defaults_to_repo_harness_foundry_plugin():
    validator = load_validator_module()

    args = validator.parse_args([])

    assert args.plugin_root == PLUGIN_ROOT


def test_validate_plugin_package_script_passes_for_default_plugin_root():
    result = run_validator()

    assert result.returncode == 0, result.stdout + result.stderr
    assert "harness-foundry plugin package validation passed" in result.stdout


def test_validate_plugin_package_script_accepts_explicit_plugin_root(tmp_path):
    plugin = copy_plugin(tmp_path)

    result = run_validator(plugin)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "harness-foundry plugin package validation passed" in result.stdout


def test_validator_rejects_manifest_components_outside_v1(tmp_path):
    plugin = copy_plugin(tmp_path)
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["mcpServers"] = {}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "non-v1 keys" in result.stdout


def test_validator_rejects_missing_manifest_file(tmp_path):
    plugin = copy_plugin(tmp_path)
    (plugin / ".codex-plugin" / "plugin.json").unlink()

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing required file: .codex-plugin/plugin.json" in result.stdout


def test_validator_rejects_missing_manifest_required_key(tmp_path):
    plugin = copy_plugin(tmp_path)
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["license"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing required keys" in result.stdout


def test_validator_rejects_missing_skills_directory(tmp_path):
    plugin = copy_plugin(tmp_path)
    shutil.rmtree(plugin / "skills")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing required directory: skills" in result.stdout


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


def test_validator_rejects_missing_boundary_file(tmp_path):
    plugin = copy_plugin(tmp_path)
    (plugin / "README.ko.md").unlink()

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing required file: README.ko.md" in result.stdout


def test_validator_rejects_extra_reference_file(tmp_path):
    plugin = copy_plugin(tmp_path)
    extra_reference = plugin / "references" / ("improvement-" + "report-template.md")
    extra_reference.write_text("# Lab-only template\n", encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "reference files mismatch" in result.stdout


def test_validator_rejects_plugin_root_scripts_directory(tmp_path):
    plugin = copy_plugin(tmp_path)
    extra_script_dir = plugin / "scripts"
    extra_script_dir.mkdir(exist_ok=True)
    extra_script = extra_script_dir / ("validate_" + "harness_foundry.py")
    extra_script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "plugin root must not include scripts directory" in result.stdout


def test_validator_rejects_plugin_root_scripts_directory_with_nested_non_py_file(tmp_path):
    plugin = copy_plugin(tmp_path)
    nested_dir = plugin / "scripts" / "nested"
    nested_dir.mkdir(parents=True)
    (nested_dir / "notes.txt").write_text("lab-only script notes\n", encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "plugin root must not include scripts directory" in result.stdout


def test_validator_rejects_plugin_root_tests_directory(tmp_path):
    plugin = copy_plugin(tmp_path)
    tests_dir = plugin / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_plugin_surface.py").write_text("# lab-only test\n", encoding="utf-8")

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "plugin root must not include tests directory" in result.stdout


def test_validator_rejects_missing_required_skill_local_script(tmp_path):
    plugin = copy_plugin(tmp_path)
    (
        plugin
        / "skills"
        / "audit-domain-harness"
        / "scripts"
        / "validate_domain_harness.py"
    ).unlink()

    result = run_validator(plugin)

    assert result.returncode == 1
    assert "missing required skill-local script files" in result.stdout


def test_readmes_list_all_skills():
    english = read_plugin_file("README.md")
    korean = read_plugin_file("README.ko.md")
    for skill in SKILLS:
        assert skill in english
        assert skill in korean


def test_readmes_separate_public_validator_from_lab_validation():
    english = read_plugin_file("README.md")
    korean = read_plugin_file("README.ko.md")
    combined = english + "\n" + korean

    assert (
        "skills/audit-domain-harness/scripts/validate_domain_harness.py <project-root>"
        in combined
    )
    assert "`docs/domain-harness/**`" in english
    assert "`docs/domain-harness/**`" in korean
    assert "Maintainer-only plugin package and corpus validation lives in" in english
    assert "plugin package" in korean
    assert "corpus" in korean


def test_skills_keep_v1_boundaries():
    combined = "\n".join(read_plugin_file(f"skills/{skill}/SKILL.md") for skill in SKILLS)
    assert "Do not recommend bulk-installing public awesome repositories." in combined
    assert (
        "AGENTS.md, MCP configuration, hooks, and subagents require separate explicit approval"
        in combined
    )
    assert "index.json" in read_plugin_file("skills/update-registry/SKILL.md")


def test_korean_readme_is_supplementary():
    korean = read_plugin_file("README.ko.md")
    assert "`SKILL.md`" in korean
    assert "canonical" in korean


def test_required_references_exist():
    for reference_file in REFERENCE_FILES:
        assert (PLUGIN_ROOT / "references" / reference_file).is_file()


def test_readmes_do_not_expose_downstream_loop():
    combined = read_plugin_file("README.md") + "\n" + read_plugin_file("README.ko.md")
    for phrase in (
        "Downstream " + "Quality Loop",
        "Downstream " + "Adoption Models",
        "Operator-" + "run",
        "Project-local " + "tooling",
        "Plugin-mediated " + "workflow",
        "privacy_" + "sanitization_check",
    ):
        assert phrase not in combined


def test_scaffold_skill_requires_downstream_approval_gates():
    text = read_plugin_file("skills/scaffold-domain-harness/SKILL.md")
    for phrase in (
        "Phase 0",
        "docs/domain-harness/** files require explicit approval",
        "diff preview",
        "rollback note",
        "GitHub issue and PR templates are outside the v1 public plugin scaffold flow.",
    ):
        assert phrase in text


def test_audit_skill_stays_in_public_plugin_scope():
    text = read_plugin_file("skills/audit-domain-harness/SKILL.md")
    assert "Perform a read-only audit" in text
    assert "Findings ordered by severity" in text
    assert "scripts/validate_domain_harness.py <project-root>" in text
    assert "read-only" in text
    for phrase in (
        "downstream",
        "upstream " + "plugin issue",
        "privacy_" + "sanitization_check",
    ):
        assert phrase not in text
