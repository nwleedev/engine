from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INTEROP = Path(__file__).resolve().parent
if str(INTEROP) not in sys.path:
    sys.path.insert(0, str(INTEROP))

from plugin_manifest_helpers import write_json, write_minimal_generated_root
from tools.build.generated_registry import registry_document, registry_entry
from tools.build.headers import GENERATED_NOTICE, markdown_header, python_header
from tools.build.validators import validate_generated_headers, validate_marketplaces


MANIFEST_REGISTRY_ENTRY = registry_entry(
    ".codex-plugin/plugin.json",
    "plugin-sources/marketplace.yaml",
)
README_SOURCE = "plugin-sources/session-memory/README.md"
PYTHON_SOURCE = "packages/session-memory/scripts/status.py"
TOML_SOURCE = "packages/session-memory/settings.toml"


def _write_text(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_valid_generated_root(root: Path) -> None:
    write_minimal_generated_root(root, manifest_name="codex-session-memory")
    write_json(
        root,
        "plugins/codex/session-memory/.generated.json",
        registry_document([MANIFEST_REGISTRY_ENTRY]),
    )


def test_registry_entry_returns_target_source_and_notice() -> None:
    assert registry_entry(
        "skills/checkpoint/SKILL.md",
        "plugin-sources/session-memory/skills/checkpoint/SKILL.md",
    ) == {
        "target": "skills/checkpoint/SKILL.md",
        "source": "plugin-sources/session-memory/skills/checkpoint/SKILL.md",
        "notice": GENERATED_NOTICE,
    }


def test_registry_document_sorts_entries_by_target() -> None:
    document = registry_document(
        [
            registry_entry("scripts/status.py", "packages/session-memory/status.py"),
            registry_entry("README.md", "plugin-sources/session-memory/README.md"),
        ]
    )

    assert document == {
        "generated": [
            {
                "target": "README.md",
                "source": "plugin-sources/session-memory/README.md",
                "notice": GENERATED_NOTICE,
            },
            {
                "target": "scripts/status.py",
                "source": "packages/session-memory/status.py",
                "notice": GENERATED_NOTICE,
            },
        ]
    }


def test_validate_generated_headers_accepts_inline_and_registry_generated_tracing(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, README_SOURCE, "# Session memory source\n")
    _write_text(tmp_path, PYTHON_SOURCE, "VALUE = 1\n")
    _write_text(
        tmp_path,
        "plugins/codex/session-memory/scripts/status.py",
        python_header(PYTHON_SOURCE) + "VALUE = 1\n",
    )
    _write_text(
        tmp_path,
        "plugins/codex/session-memory/README.md",
        "# Session memory\n",
    )
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document(
            [
                MANIFEST_REGISTRY_ENTRY,
                registry_entry(
                    "README.md",
                    README_SOURCE,
                )
            ]
        ),
    )

    assert validate_generated_headers(tmp_path) == []


@pytest.mark.parametrize("extension", [".py", ".md", ".toml", ".json"])
def test_validate_generated_headers_rejects_generated_file_without_tracing(
    tmp_path: Path,
    extension: str,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(
        tmp_path,
        f"plugins/codex/session-memory/untraced{extension}",
        "untraced = true\n",
    )

    errors = validate_generated_headers(tmp_path)

    assert any("missing generated tracing" in error for error in errors)
    assert any(f"plugins/codex/session-memory/untraced{extension}" in error for error in errors)


def test_validate_generated_headers_accepts_json_file_with_registry_tracing(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(
        tmp_path,
        "plugin-sources/session-memory/adapters/codex/hooks/hooks.json",
        "{}\n",
    )
    write_json(
        tmp_path,
        "plugins/codex/session-memory/hooks/hooks.json",
        {"hooks": {}},
    )
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document(
            [
                MANIFEST_REGISTRY_ENTRY,
                registry_entry(
                    "hooks/hooks.json",
                    "plugin-sources/session-memory/adapters/codex/hooks/hooks.json",
                )
            ]
        ),
    )

    assert validate_generated_headers(tmp_path) == []


@pytest.mark.parametrize(
    "target",
    [
        "",
        ".",
        "./README.md",
        "docs/./README.md",
        "../outside.md",
        "references/../../outside.md",
        "/absolute.md",
        "foo\\bar.md",
        ".generated.json",
    ],
)
def test_validate_generated_headers_rejects_registry_target_outside_plugin_root(
    tmp_path: Path,
    target: str,
) -> None:
    _write_valid_generated_root(tmp_path)
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document(
            [
                registry_entry(
                    target,
                    "plugin-sources/session-memory/README.md",
                )
            ]
        ),
    )

    errors = validate_generated_headers(tmp_path)

    assert any("unsafe generated registry target" in error for error in errors)


@pytest.mark.parametrize(
    "source",
    [
        "",
        ".",
        "plugin-sources/./session-memory/README.md",
        "packages/./x.py",
        "docs/session-memory/README.md",
        "plugin-sources/../secrets.md",
        "/abs/source.md",
        "packages\\x.py",
    ],
)
def test_validate_generated_headers_rejects_registry_source_outside_generated_sources(
    tmp_path: Path,
    source: str,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, "plugins/codex/session-memory/README.md", "# Session memory\n")
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document([registry_entry("README.md", source)]),
    )

    errors = validate_generated_headers(tmp_path)

    assert any("invalid generated registry source" in error for error in errors)


def test_validate_generated_headers_rejects_registry_entry_pointing_to_missing_file(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, README_SOURCE, "# Session memory source\n")
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document(
            [
                registry_entry(
                    "README.md",
                    "plugin-sources/session-memory/README.md",
                )
            ]
        ),
    )

    errors = validate_generated_headers(tmp_path)

    assert any("generated registry target is missing" in error for error in errors)
    assert any("plugins/codex/session-memory/README.md" in error for error in errors)


def test_validate_generated_headers_rejects_registry_entry_pointing_to_missing_source(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, "plugins/codex/session-memory/README.md", "# Session memory\n")
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        registry_document(
            [
                registry_entry(
                    "README.md",
                    "plugin-sources/session-memory/missing.md",
                )
            ]
        ),
    )

    errors = validate_generated_headers(tmp_path)

    assert any("generated registry source is missing" in error for error in errors)
    assert any("plugin-sources/session-memory/missing.md" in error for error in errors)


@pytest.mark.parametrize("missing_field", ["target", "source", "notice"])
def test_validate_generated_headers_rejects_malformed_registry_entries(
    tmp_path: Path,
    missing_field: str,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(
        tmp_path,
        "plugins/codex/session-memory/README.md",
        markdown_header("plugin-sources/session-memory/README.md") + "# Session memory\n",
    )
    entry = registry_entry("README.md", "plugin-sources/session-memory/README.md")
    del entry[missing_field]
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        {"generated": [entry]},
    )

    errors = validate_generated_headers(tmp_path)

    assert any("malformed generated registry entry" in error for error in errors)


def test_validate_generated_headers_rejects_duplicate_registry_targets(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, README_SOURCE, "# Session memory source\n")
    _write_text(tmp_path, "packages/session-memory/README.md", "# Package source\n")
    _write_text(tmp_path, "plugins/codex/session-memory/README.md", "# Session memory\n")
    write_json(
        tmp_path,
        "plugins/codex/session-memory/.generated.json",
        {
            "generated": [
                registry_entry("README.md", "plugin-sources/session-memory/README.md"),
                registry_entry("README.md", "packages/session-memory/README.md"),
            ]
        },
    )

    errors = validate_generated_headers(tmp_path)

    assert any("duplicate generated registry target" in error for error in errors)


def test_validate_generated_headers_rejects_inline_header_after_body_text(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(
        tmp_path,
        "plugins/codex/session-memory/README.md",
        "# Session memory\n" + markdown_header("plugin-sources/session-memory/README.md"),
    )

    errors = validate_generated_headers(tmp_path)

    assert any("missing generated tracing" in error for error in errors)
    assert any("plugins/codex/session-memory/README.md" in error for error in errors)


@pytest.mark.parametrize(
    ("relative_path", "text", "source"),
    [
        (
            "plugins/codex/session-memory/README.md",
            markdown_header(README_SOURCE) + "# Session memory\n",
            README_SOURCE,
        ),
        (
            "plugins/codex/session-memory/status.py",
            python_header(PYTHON_SOURCE) + "VALUE = 1\n",
            PYTHON_SOURCE,
        ),
        (
            "plugins/codex/session-memory/settings.toml",
            python_header(TOML_SOURCE) + "enabled = true\n",
            TOML_SOURCE,
        ),
    ],
)
def test_validate_generated_headers_accepts_exact_inline_headers(
    tmp_path: Path,
    relative_path: str,
    text: str,
    source: str,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(tmp_path, source, "source\n")
    _write_text(tmp_path, relative_path, text)

    assert validate_generated_headers(tmp_path) == []


def test_validate_generated_headers_rejects_inline_header_pointing_to_missing_source(
    tmp_path: Path,
) -> None:
    _write_valid_generated_root(tmp_path)
    _write_text(
        tmp_path,
        "plugins/codex/session-memory/README.md",
        markdown_header("plugin-sources/session-memory/missing.md") + "# Session memory\n",
    )

    errors = validate_generated_headers(tmp_path)

    assert any("missing generated tracing" in error for error in errors)
    assert any("plugins/codex/session-memory/README.md" in error for error in errors)
