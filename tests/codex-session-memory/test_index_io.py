from pathlib import Path
import index_io as io


def test_create_new_index(tmp_path):
    p = tmp_path / "INDEX.md"
    io.write_index(p, {"session_id": "abc", "cwd": "/r", "started": "T0",
                       "last_updated": "T0", "last_processed_offset": 0,
                       "jsonl_path": "/x.jsonl"}, contexts=[])
    text = p.read_text()
    assert "session_id: abc" in text
    assert "## 컨텍스트 목록" in text


def test_read_index_frontmatter(tmp_path):
    p = tmp_path / "INDEX.md"
    p.write_text(
        "---\n"
        "session_id: abc\n"
        "last_processed_offset: 1234\n"
        "last_updated: 2026-05-01T10:00:00\n"
        "---\n\n# 세션 요약\n\n## 컨텍스트 목록\n\n- [foo.md] — bar\n"
    )
    fm = io.read_frontmatter(p)
    assert fm["session_id"] == "abc"
    assert fm["last_processed_offset"] == 1234


def test_append_context_entry(tmp_path):
    p = tmp_path / "INDEX.md"
    io.write_index(p, {"session_id": "abc", "cwd": "/r", "started": "T0",
                       "last_updated": "T0", "last_processed_offset": 0,
                       "jsonl_path": "/x.jsonl"}, contexts=[])
    io.append_context_entry(p, filename="CONTEXT-20260501-1000-foo.md", summary="first save")
    text = p.read_text()
    assert "[CONTEXT-20260501-1000-foo.md] — first save" in text


def test_update_frontmatter_preserves_body(tmp_path):
    p = tmp_path / "INDEX.md"
    io.write_index(p, {"session_id": "abc", "cwd": "/r", "started": "T0",
                       "last_updated": "T0", "last_processed_offset": 0,
                       "jsonl_path": "/x.jsonl"}, contexts=[])
    io.append_context_entry(p, filename="A.md", summary="aa")
    io.update_frontmatter(p, last_processed_offset=999, last_updated="T1")
    text = p.read_text()
    fm = io.read_frontmatter(p)
    assert fm["last_processed_offset"] == 999
    assert fm["last_updated"] == "T1"
    assert "[A.md] — aa" in text


def test_returns_none_for_missing(tmp_path):
    assert io.read_frontmatter(tmp_path / "missing.md") is None
