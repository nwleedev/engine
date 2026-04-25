"""Cross-plugin contract: ref-manager writes INDEX.md; quality-guard reads it.

The contract is:
  <cwd>/.claude/refs/INDEX.md  — markdown table written by ref_io.save_index
  read by quality-guard's ref_index_reader.read_index as raw text
"""
import sys
from pathlib import Path

REF_SCRIPTS = Path(__file__).parent.parent.parent / "plugins/ref-manager/scripts"
QG_SCRIPTS = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(REF_SCRIPTS))
sys.path.insert(0, str(QG_SCRIPTS))

import ref_io
import ref_index_reader


def test_written_index_is_readable_by_quality_guard(tmp_path):
    entries = [
        {"name": "python-typing", "path": ".claude/refs/python/typing.md", "tags": ["python", "stdlib"]},
        {"name": "clean-arch", "path": ".claude/refs/arch/clean-arch.pdf", "tags": ["architecture"]},
    ]
    ref_io.save_index(str(tmp_path), entries)
    raw = ref_index_reader.read_index(str(tmp_path))
    assert "python-typing" in raw
    assert "clean-arch" in raw
    assert ".claude/refs/python/typing.md" in raw
    assert "python, stdlib" in raw


def test_empty_index_returns_empty_string_for_quality_guard(tmp_path):
    assert ref_index_reader.read_index(str(tmp_path)) == ""


def test_index_written_by_add_entry_is_readable(tmp_path):
    ref_io.add_entry(str(tmp_path), "my-ref", ".claude/refs/topic/doc.md", ["tag1", "tag2"])
    raw = ref_index_reader.read_index(str(tmp_path))
    assert "my-ref" in raw
    assert "tag1, tag2" in raw


def test_user_prompt_handler_injects_refs_when_index_exists(tmp_path):
    """End-to-end: written index causes quality-guard to inject quality-instruction."""
    import json
    import io
    from contextlib import redirect_stdout

    import user_prompt_handler as uph

    ref_io.add_entry(str(tmp_path), "api-spec", ".claude/refs/api/spec.md", ["api"])

    payload = json.dumps({"cwd": str(tmp_path), "prompt": "How do I call the API?"})
    buf = io.StringIO()
    with __import__("unittest.mock", fromlist=["patch"]).patch("sys.stdin", io.StringIO(payload)):
        with redirect_stdout(buf):
            uph.main()

    output = json.loads(buf.getvalue().strip())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "quality-instruction" in context
    assert "api-spec" in context


def test_user_prompt_handler_falls_back_to_debiasing_when_no_refs(tmp_path):
    """No refs → quality-guard injects cognitive debiasing instead."""
    import json
    import io
    from contextlib import redirect_stdout

    import user_prompt_handler as uph

    payload = json.dumps({"cwd": str(tmp_path), "prompt": "Explain caching."})
    buf = io.StringIO()
    with __import__("unittest.mock", fromlist=["patch"]).patch("sys.stdin", io.StringIO(payload)):
        with redirect_stdout(buf):
            uph.main()

    output = json.loads(buf.getvalue().strip())
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "cognitive-debiasing" in context
    assert "quality-instruction" not in context
