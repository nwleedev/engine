from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CODEX_LEARNABLE = ROOT / "plugins" / "codex" / "learnable"
CLAUDE_LEARNABLE = ROOT / "plugins" / "claude" / "learnable"
FORBIDDEN_RUNTIME_DEPENDENCIES = {
    "fastapi",
    "starlette",
    "flask",
    "uvicorn",
}


def _registry_targets() -> dict[str, str]:
    registry = json.loads((CODEX_LEARNABLE / ".generated.json").read_text(encoding="utf-8"))
    return {
        entry["target"]: entry["source"]
        for entry in registry["generated"]
    }


def test_learnable_codex_artifact_contains_mvp_entrypoints() -> None:
    assert (CODEX_LEARNABLE / ".codex-plugin/plugin.json").is_file()
    assert (CODEX_LEARNABLE / "skills/entry/SKILL.md").is_file()
    assert (CODEX_LEARNABLE / "references/policy.md").is_file()
    assert (CODEX_LEARNABLE / "_packages/learnable/__init__.py").is_file()
    assert (CODEX_LEARNABLE / "_packages/learnable/static/index.html").is_file()
    assert (CODEX_LEARNABLE / "_packages/learnable/schemas/session.schema.json").is_file()


def test_learnable_mvp_does_not_generate_claude_artifact() -> None:
    assert not CLAUDE_LEARNABLE.exists()


def test_learnable_generated_registry_traces_sources() -> None:
    targets = _registry_targets()

    expected_sources = {
        ".codex-plugin/plugin.json": "plugin-sources/marketplace.yaml",
        "skills/entry/SKILL.md": "plugin-sources/learnable/adapters/codex/skills/entry/SKILL.md",
        "references/policy.md": "plugin-sources/learnable/references/policy.md",
        "_packages/learnable/__init__.py": "packages/learnable/learnable/__init__.py",
        "_packages/learnable/static/index.html": "packages/learnable/learnable/static/index.html",
        "_packages/learnable/static/app.css": "packages/learnable/learnable/static/app.css",
        "_packages/learnable/static/app.js": "packages/learnable/learnable/static/app.js",
        "_packages/learnable/schemas/session.schema.json": "packages/learnable/learnable/schemas/session.schema.json",
    }
    for target, source in expected_sources.items():
        assert targets[target] == source


def test_learnable_generated_skill_links_resolve_inside_artifact() -> None:
    for skill_path in sorted((CODEX_LEARNABLE / "skills").glob("*/SKILL.md")):
        skill = skill_path.read_text(encoding="utf-8")
        assert "../../../../references/" not in skill
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill):
            if link.startswith(("http://", "https://", "#")):
                continue
            assert (skill_path.parent / link).resolve().is_file(), (
                f"{skill_path.relative_to(CODEX_LEARNABLE)}: {link}"
            )


def test_learnable_mvp_has_no_external_web_runtime_dependency_requirement() -> None:
    manifest = json.loads(
        (CODEX_LEARNABLE / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    artifact_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in CODEX_LEARNABLE.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md", ".py", ".toml"}
    )

    assert "dependencies" not in manifest
    for dependency in FORBIDDEN_RUNTIME_DEPENDENCIES:
        assert dependency not in artifact_text
    assert not (CODEX_LEARNABLE / "package.json").exists()
    assert not (CODEX_LEARNABLE / "node_modules").exists()
