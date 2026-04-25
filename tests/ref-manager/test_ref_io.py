import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/ref-manager/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import ref_io


def test_get_refs_dir(tmp_path):
    result = ref_io.get_refs_dir(str(tmp_path))
    assert result == tmp_path / ".claude" / "refs"


def test_get_index_path(tmp_path):
    result = ref_io.get_index_path(str(tmp_path))
    assert result == tmp_path / ".claude" / "refs" / "INDEX.md"


def test_load_index_returns_empty_when_no_file(tmp_path):
    entries = ref_io.load_index(str(tmp_path))
    assert entries == []


def test_save_and_load_index_roundtrip(tmp_path):
    entries = [
        {"name": "Python Typing Docs", "path": ".claude/refs/python/typing-docs.md", "tags": ["python", "types"]},
        {"name": "Clean Code", "path": ".claude/refs/general/clean-code.pdf", "tags": ["architecture"]},
    ]
    ref_io.save_index(str(tmp_path), entries)
    loaded = ref_io.load_index(str(tmp_path))
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Python Typing Docs"
    assert loaded[0]["path"] == ".claude/refs/python/typing-docs.md"
    assert "python" in loaded[0]["tags"]
    assert loaded[1]["name"] == "Clean Code"


def test_save_index_creates_directory(tmp_path):
    entries = [{"name": "Foo", "path": ".claude/refs/foo/bar.md", "tags": []}]
    ref_io.save_index(str(tmp_path), entries)
    index_path = tmp_path / ".claude" / "refs" / "INDEX.md"
    assert index_path.exists()


def test_save_index_writes_markdown_table(tmp_path):
    entries = [{"name": "MyRef", "path": ".claude/refs/x/y.md", "tags": ["a", "b"]}]
    ref_io.save_index(str(tmp_path), entries)
    content = (tmp_path / ".claude" / "refs" / "INDEX.md").read_text(encoding="utf-8")
    assert "# Refs Index" in content
    assert "| Name | Path | Tags |" in content
    assert "MyRef" in content
    assert ".claude/refs/x/y.md" in content
    assert "a, b" in content


def test_add_entry_appends_to_existing_index(tmp_path):
    initial = [{"name": "Existing", "path": ".claude/refs/e/e.md", "tags": ["x"]}]
    ref_io.save_index(str(tmp_path), initial)
    ref_io.add_entry(str(tmp_path), "NewRef", ".claude/refs/n/n.pdf", ["y", "z"])
    loaded = ref_io.load_index(str(tmp_path))
    names = [e["name"] for e in loaded]
    assert "Existing" in names
    assert "NewRef" in names


def test_add_entry_on_empty_index(tmp_path):
    ref_io.add_entry(str(tmp_path), "First", ".claude/refs/f/first.md", ["tag1"])
    loaded = ref_io.load_index(str(tmp_path))
    assert len(loaded) == 1
    assert loaded[0]["name"] == "First"


def test_load_index_parses_tags_as_list(tmp_path):
    entries = [{"name": "Multi", "path": ".claude/refs/m/multi.md", "tags": ["a", "b", "c"]}]
    ref_io.save_index(str(tmp_path), entries)
    loaded = ref_io.load_index(str(tmp_path))
    assert loaded[0]["tags"] == ["a", "b", "c"]


def test_load_index_handles_empty_tags(tmp_path):
    entries = [{"name": "NoTags", "path": ".claude/refs/n/notags.md", "tags": []}]
    ref_io.save_index(str(tmp_path), entries)
    loaded = ref_io.load_index(str(tmp_path))
    assert loaded[0]["tags"] == []


def test_add_entry_deduplicates_by_name(tmp_path):
    ref_io.add_entry(str(tmp_path), "dup", ".claude/refs/a/doc.md", ["x"])
    ref_io.add_entry(str(tmp_path), "dup", ".claude/refs/b/doc.md", ["y"])
    loaded = ref_io.load_index(str(tmp_path))
    assert len(loaded) == 1
    assert loaded[0]["path"] == ".claude/refs/b/doc.md"


def test_pipe_character_in_fields_roundtrips_correctly(tmp_path):
    entries = [{"name": "foo|bar", "path": ".claude/refs/t/doc.md", "tags": ["tag|1"]}]
    ref_io.save_index(str(tmp_path), entries)
    loaded = ref_io.load_index(str(tmp_path))
    assert loaded[0]["name"] == "foo|bar"
    assert loaded[0]["tags"] == ["tag|1"]
