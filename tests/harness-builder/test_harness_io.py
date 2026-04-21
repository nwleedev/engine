import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-builder/scripts"

_spec = importlib.util.spec_from_file_location(
    "harness_builder.harness_io", SCRIPTS_DIR / "harness_io.py"
)
assert _spec is not None and _spec.loader is not None
hio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hio)

SAMPLE = """\
---
domain: nextjs-typescript
domain_type: code
languages: [TypeScript]
frameworks: [Next.js, Tailwind CSS]
linters: [eslint, prettier]
file_patterns: ["*.tsx", "app/**"]
keywords: [component, hook, page]
updated: 2026-04-21
---

# Next.js Harness

## Purpose
Enforce type-safe React component patterns.

## Core Rules
- [ ] Use named exports for components

## Pattern Examples

<Good>
export function Button() { return <button /> }
</Good>

<Bad>
export default () => <button />
</Bad>

## Anti-Pattern Gate
Is this component reusable?
"""


def test_parse_frontmatter_extracts_domain():
    fm = hio.parse_frontmatter(SAMPLE)
    assert fm["domain"] == "nextjs-typescript"


def test_parse_frontmatter_extracts_domain_type():
    fm = hio.parse_frontmatter(SAMPLE)
    assert fm["domain_type"] == "code"


def test_parse_frontmatter_extracts_language_list():
    fm = hio.parse_frontmatter(SAMPLE)
    assert fm["languages"] == ["TypeScript"]


def test_parse_frontmatter_extracts_framework_list():
    fm = hio.parse_frontmatter(SAMPLE)
    assert "Next.js" in fm["frameworks"]
    assert "Tailwind CSS" in fm["frameworks"]


def test_parse_frontmatter_extracts_file_patterns():
    fm = hio.parse_frontmatter(SAMPLE)
    assert "*.tsx" in fm["file_patterns"]
    assert "app/**" in fm["file_patterns"]


def test_parse_frontmatter_returns_empty_on_missing_marker():
    fm = hio.parse_frontmatter("# No frontmatter here")
    assert fm == {}


def test_has_harness_dir_false_when_missing(tmp_path):
    assert hio.has_harness_dir(str(tmp_path)) is False


def test_has_harness_dir_true_when_present(tmp_path):
    (tmp_path / ".claude" / "harness").mkdir(parents=True)
    assert hio.has_harness_dir(str(tmp_path)) is True


def test_write_creates_directory_and_file(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    hio.write_harness_file(str(harness_dir), "nextjs-typescript", SAMPLE)
    assert (harness_dir / "nextjs-typescript.md").exists()


def test_write_returns_file_path(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    path = hio.write_harness_file(str(harness_dir), "test-domain", SAMPLE)
    assert path.endswith("test-domain.md")


def test_read_harness_files_returns_list(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    hio.write_harness_file(str(harness_dir), "nextjs-typescript", SAMPLE)
    files = hio.read_harness_files(str(harness_dir))
    assert len(files) == 1


def test_read_harness_files_parses_domain(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    hio.write_harness_file(str(harness_dir), "nextjs-typescript", SAMPLE)
    files = hio.read_harness_files(str(harness_dir))
    assert files[0]["domain"] == "nextjs-typescript"


def test_read_harness_files_empty_dir_returns_empty(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    harness_dir.mkdir(parents=True)
    files = hio.read_harness_files(str(harness_dir))
    assert files == []


def test_read_harness_files_missing_dir_returns_empty(tmp_path):
    files = hio.read_harness_files(str(tmp_path / "nonexistent"))
    assert files == []


def test_harness_file_exists_true(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    hio.write_harness_file(str(harness_dir), "my-domain", SAMPLE)
    assert hio.harness_file_exists(str(harness_dir), "my-domain") is True


def test_harness_file_exists_false(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    harness_dir.mkdir(parents=True)
    assert hio.harness_file_exists(str(harness_dir), "nonexistent") is False


def test_read_all_harness_content_includes_domain_header(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    hio.write_harness_file(str(harness_dir), "nextjs-typescript", SAMPLE)
    content = hio.read_all_harness_content(str(harness_dir))
    assert "nextjs-typescript" in content


def test_read_all_harness_content_empty_dir_returns_empty(tmp_path):
    harness_dir = tmp_path / ".claude" / "harness"
    harness_dir.mkdir(parents=True)
    assert hio.read_all_harness_content(str(harness_dir)) == ""
