from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# pytest importlib mode does not add the project root for this interop import.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from renderers.codex.skills import render_codex_skill_tree
from tools.build.headers import markdown_header


def test_codex_skill_rendering_adds_generated_header_with_source_path() -> None:
    files = render_codex_skill_tree(ROOT / "plugin-sources" / "shared-skills")
    source_path = "plugin-sources/shared-skills/skills/requirements-packet/SKILL.md"

    text = files["skills/requirements-packet/SKILL.md"]

    assert text.startswith("---\n")
    assert f"\n---\n{markdown_header(source_path)}" in text
    assert "name: requirements-packet" in text


def test_codex_skill_rendering_includes_reference_documents() -> None:
    files = render_codex_skill_tree(ROOT / "plugin-sources" / "shared-skills")

    assert "references/comment-specs-by-stack.md" in files
    assert files["references/comment-specs-by-stack.md"].startswith(
        markdown_header("plugin-sources/shared-skills/references/comment-specs-by-stack.md")
    )


def test_codex_skill_rendering_includes_python_support_files() -> None:
    files = render_codex_skill_tree(ROOT / "plugin-sources" / "shared-skills")

    target = "skills/spec-plan-coverage/validate_spec_plan_coverage.py"
    assert target in files
    assert files[target].startswith(
        "# GENERATED FILE - DO NOT EDIT\n"
        "# source: plugin-sources/shared-skills/skills/spec-plan-coverage/validate_spec_plan_coverage.py\n\n"
    )


def test_codex_skill_rendering_rejects_skill_markdown_directory(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "shared-skills"
    (source_root / "skills" / "broken-skill" / "SKILL.md").mkdir(parents=True)
    (source_root / "references").mkdir(parents=True)
    monkeypatch.setattr("renderers.codex.skills.ROOT", tmp_path)

    try:
        render_codex_skill_tree(source_root)
    except ValueError as error:
        assert str(error) == (
            f"expected file: {source_root / 'skills' / 'broken-skill' / 'SKILL.md'}"
        )
    else:
        raise AssertionError("Expected ValueError for a directory matched as SKILL.md")


def test_codex_skill_rendering_rejects_reference_markdown_directory(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "shared-skills"
    skill_file = source_root / "skills" / "sample-skill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text(
        "---\nname: sample-skill\ndescription: Use when testing.\n---\n",
        encoding="utf-8",
    )
    (source_root / "references" / "broken.md").mkdir(parents=True)
    monkeypatch.setattr("renderers.codex.skills.ROOT", tmp_path)

    try:
        render_codex_skill_tree(source_root)
    except ValueError as error:
        assert str(error) == f"expected file: {source_root / 'references' / 'broken.md'}"
    else:
        raise AssertionError("Expected ValueError for a directory matched as a reference")


def test_codex_skill_rendering_rejects_symlinked_skill_source(
    tmp_path: Path, monkeypatch
) -> None:
    source_root = tmp_path / "plugin-sources" / "shared-skills"
    skill_file = source_root / "skills" / "sample-skill" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("name: outside\n", encoding="utf-8")
    skill_file.symlink_to(outside)
    (source_root / "references").mkdir()
    monkeypatch.setattr("renderers.codex.skills.ROOT", tmp_path)

    try:
        render_codex_skill_tree(source_root)
    except ValueError as error:
        assert "canonical source file must not be a symlink" in str(error)
    else:
        raise AssertionError("Expected ValueError for a symlinked SKILL.md source")
