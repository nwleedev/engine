from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import renderers.claude.subagents as claude_subagents
import renderers.codex.skills as codex_skills
import renderers.codex.subagents as codex_subagents
import renderers.plugin_tree as plugin_tree
import renderers.shared_subagents as shared_subagents
from tools.build.headers import GENERATED_NOTICE
import tools.build_plugins as build_plugins


def test_session_memory_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/session-memory/_packages/session_memory/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/session-memory/_packages/session_memory/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/codex/session-memory/_packages/session_memory/jsonl_parser.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/session-memory/_packages/session_memory/evidence_extractor.py"
    ).exists()


def test_quality_guard_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/quality-guard/_packages/quality_guard/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/quality-guard/_packages/quality_guard/__init__.py"
    ).exists()


def test_research_prompt_package_is_materialized_into_generated_artifacts() -> None:
    assert (
        ROOT / "plugins/codex/deep-research-prompt-export/_packages/research_prompt/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/deep-research-prompt-export/_packages/research_prompt/__init__.py"
    ).exists()
    assert (
        ROOT / "plugins/codex/deep-research-prompt-export/_packages/research_prompt/cli.py"
    ).exists()
    assert (
        ROOT / "plugins/claude/deep-research-prompt-export/_packages/research_prompt/redaction.py"
    ).exists()


def test_tomli_package_is_configured_for_python39_plugin_artifacts() -> None:
    artifacts = build_plugins._package_artifacts()
    tomli_source = ROOT / "packages/vendor/tomli/tomli"
    expected_targets = {
        ROOT / "plugins/codex/session-memory/_packages/tomli",
        ROOT / "plugins/claude/session-memory/_packages/tomli",
        ROOT / "plugins/codex/deep-research-prompt-export/_packages/tomli",
        ROOT / "plugins/claude/deep-research-prompt-export/_packages/tomli",
    }

    assert (tomli_source / "__init__.py").is_file()
    assert (tomli_source / "_parser.py").is_file()
    assert {
        target_root
        for source_root, target_root, package_name in artifacts
        if source_root == tomli_source and package_name == "tomli"
    } == expected_targets


def test_tomli_license_is_materialized_by_generated_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_root = tmp_path / "root"
    tmp_root.mkdir()
    shutil.copytree(ROOT / "plugin-sources", tmp_root / "plugin-sources")
    shutil.copytree(ROOT / "packages", tmp_root / "packages")
    monkeypatch.setattr(build_plugins, "ROOT", tmp_root)
    monkeypatch.setattr(codex_skills, "ROOT", tmp_root)
    monkeypatch.setattr(codex_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(claude_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(plugin_tree, "ROOT", tmp_root)
    monkeypatch.setattr(shared_subagents, "ROOT", tmp_root)

    assert build_plugins.main() == 0

    expected_license_targets = {
        tmp_root / "plugins/codex/session-memory/_packages/tomli/LICENSE",
        tmp_root / "plugins/claude/session-memory/_packages/tomli/LICENSE",
        tmp_root / "plugins/codex/deep-research-prompt-export/_packages/tomli/LICENSE",
        tmp_root / "plugins/claude/deep-research-prompt-export/_packages/tomli/LICENSE",
    }
    for license_target in expected_license_targets:
        plugin_root = license_target.parents[2]
        registry = json.loads(
            (plugin_root / ".generated.json").read_text(encoding="utf-8")
        )

        assert license_target.read_bytes() == (
            tmp_root / "packages/vendor/tomli/LICENSE"
        ).read_bytes()
        assert {
            "target": "_packages/tomli/LICENSE",
            "source": "packages/vendor/tomli/LICENSE",
            "notice": GENERATED_NOTICE,
        } in registry["generated"]


def test_renamed_research_prompt_roots_are_pruned_before_materialization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_root = tmp_path / "root"
    tmp_root.mkdir()
    shutil.copytree(ROOT / "plugin-sources", tmp_root / "plugin-sources")
    shutil.copytree(ROOT / "packages", tmp_root / "packages")
    stale_roots = [
        tmp_root / "plugins/codex/research-prompt",
        tmp_root / "plugins/claude/research-prompt",
    ]
    for stale_root in stale_roots:
        stale_root.mkdir(parents=True)
        (stale_root / "stale.txt").write_text("stale", encoding="utf-8")
        (stale_root / ".generated.json").write_text(
            json.dumps(
                {
                    "generated": [
                        {
                            "target": "stale.txt",
                            "source": "plugin-sources/marketplace.yaml",
                            "notice": GENERATED_NOTICE,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(build_plugins, "ROOT", tmp_root)
    monkeypatch.setattr(codex_skills, "ROOT", tmp_root)
    monkeypatch.setattr(codex_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(claude_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(plugin_tree, "ROOT", tmp_root)
    monkeypatch.setattr(shared_subagents, "ROOT", tmp_root)

    assert build_plugins.main() == 0

    assert all(not stale_root.exists() for stale_root in stale_roots)
    assert (
        tmp_root
        / "plugins/codex/deep-research-prompt-export/_packages/research_prompt/__init__.py"
    ).is_file()
    assert (
        tmp_root
        / "plugins/claude/deep-research-prompt-export/_packages/research_prompt/__init__.py"
    ).is_file()


def test_renamed_research_prompt_prune_preserves_untracked_manual_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_root = tmp_path / "root"
    tmp_root.mkdir()
    shutil.copytree(ROOT / "plugin-sources", tmp_root / "plugin-sources")
    shutil.copytree(ROOT / "packages", tmp_root / "packages")
    manual_root = tmp_root / "plugins/codex/research-prompt"
    manual_root.mkdir(parents=True)
    generated_file = manual_root / "generated.txt"
    generated_file.write_text("generated", encoding="utf-8")
    manual_file = manual_root / "manual-note.md"
    manual_file.write_text("manual", encoding="utf-8")
    (manual_root / ".generated.json").write_text(
        json.dumps(
            {
                "generated": [
                    {
                        "target": "generated.txt",
                        "source": "plugin-sources/marketplace.yaml",
                        "notice": GENERATED_NOTICE,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(build_plugins, "ROOT", tmp_root)
    monkeypatch.setattr(codex_skills, "ROOT", tmp_root)
    monkeypatch.setattr(codex_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(claude_subagents, "ROOT", tmp_root)
    monkeypatch.setattr(plugin_tree, "ROOT", tmp_root)
    monkeypatch.setattr(shared_subagents, "ROOT", tmp_root)

    assert build_plugins.main() == 0

    assert manual_file.read_text(encoding="utf-8") == "manual"
    assert generated_file.read_text(encoding="utf-8") == "generated"


def test_package_artifacts_are_grouped_by_generated_plugin_root() -> None:
    artifacts_by_target_root = build_plugins._package_artifacts_by_target_root(
        build_plugins._package_artifacts()
    )

    assert artifacts_by_target_root[
        ROOT / "plugins/codex/session-memory"
    ] == [
        (ROOT / "packages/session-memory/session_memory", "_packages/session_memory/"),
        (ROOT / "packages/vendor/tomli/tomli", "_packages/tomli/"),
    ]
    assert artifacts_by_target_root[
        ROOT / "plugins/claude/deep-research-prompt-export"
    ] == [
        (ROOT / "packages/deep-research-prompt-export/research_prompt", "_packages/research_prompt/"),
        (ROOT / "packages/vendor/tomli/tomli", "_packages/tomli/"),
    ]


def test_research_prompt_generated_wrappers_run_with_defaults(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    env = {**os.environ, "RESEARCH_PROMPT_DATE": "2026-05-13"}

    subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "plugins/codex/deep-research-prompt-export/skills/deep-research-prompt-export/scripts/research_prompt.py"
            ),
            "--harness",
            "codex",
            "--problem",
            "Wrapper defaults",
        ],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "plugins/claude/deep-research-prompt-export/scripts/research_prompt.py"),
            "--harness",
            "claude",
            "--problem",
            "Wrapper defaults",
        ],
        cwd=project,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        project / ".codex/deep-research-prompts/2026-05-13-wrapper-defaults.md"
    ).exists()
    assert (
        project / ".claude/deep-research-prompts/2026-05-13-wrapper-defaults.md"
    ).exists()
