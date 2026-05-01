import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "codex-session-memory"


def read_frontmatter_name(skill_md: Path) -> str:
    assert skill_md.exists(), f"missing skill markdown: {skill_md}"
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    assert lines, f"empty skill markdown: {skill_md}"
    assert lines[0] == "---"
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("name: "):
            return line.removeprefix("name: ").strip()
    raise AssertionError(f"missing name frontmatter in {skill_md}")


def load_resume_module():
    path = PLUGIN_ROOT / "skills" / "resume" / "resume.py"
    assert path.exists(), f"missing resume module: {path}"
    module_name = "codex_session_memory_resume"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_plugin_version_is_0_2_0():
    manifest_path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    assert manifest_path.exists(), f"missing plugin manifest: {manifest_path}"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["version"] == "0.2.0"


def test_skill_directories_and_frontmatter_use_short_names():
    expected = {"checkpoint", "resume", "status"}
    skill_root = PLUGIN_ROOT / "skills"
    assert skill_root.is_dir(), f"missing skills directory: {skill_root}"

    actual = {p.name for p in skill_root.iterdir() if p.is_dir() and not p.name.startswith("__")}

    assert actual == expected
    for name in expected:
        skill_md = skill_root / name / "SKILL.md"
        assert skill_md.exists(), f"missing skill markdown: {skill_md}"
        assert read_frontmatter_name(skill_md) == name


@pytest.mark.parametrize("readme", ["README.md", "README.ko.md"])
def test_readme_documents_short_invocations_only(readme):
    readme_path = PLUGIN_ROOT / readme
    assert readme_path.exists(), f"missing README: {readme_path}"
    content = readme_path.read_text(encoding="utf-8")

    assert "$codex-session-memory:checkpoint" in content
    assert "$codex-session-memory:resume [prefix]" in content
    assert "$codex-session-memory:status" in content
    assert "$codex-session-memory:session-memory-checkpoint" not in content
    assert "$codex-session-memory:session-memory-resume" not in content
    assert "$codex-session-memory:session-memory-status" not in content


def test_resume_table_hint_uses_short_invocation():
    resume = load_resume_module()
    table = resume.render_table([
        {
            "session_id": "abcdef123456",
            "last_updated": "2026-05-01T00:00:00Z",
            "path": Path("INDEX.md"),
        }
    ])

    assert "Call `$codex-session-memory:resume <8-char-prefix>` to inject one." in table
    assert "$codex-session-memory:session-memory-resume" not in table
    assert "$session-memory-resume" not in table
