# tests/quality-guard/test_superficial_detector.py
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/quality-guard/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import superficial_detector as sd


# --- parse_verdict ---

def test_parse_verdict_superficial_high():
    response = "VERDICT: superficial\nREASON: silences exception\nCONFIDENCE: high"
    verdict, reason, confidence = sd.parse_verdict(response)
    assert verdict == "superficial"
    assert reason == "silences exception"
    assert confidence == "high"

def test_parse_verdict_structural_high():
    response = "VERDICT: structural\nREASON: fixes root logic\nCONFIDENCE: high"
    verdict, reason, confidence = sd.parse_verdict(response)
    assert verdict == "structural"
    assert confidence == "high"

def test_parse_verdict_unclear():
    response = "VERDICT: unclear\nREASON: ambiguous change\nCONFIDENCE: low"
    verdict, _, confidence = sd.parse_verdict(response)
    assert verdict == "unclear"
    assert confidence == "low"

def test_parse_verdict_case_insensitive():
    response = "VERDICT: Superficial\nREASON: bad\nCONFIDENCE: High"
    verdict, _, confidence = sd.parse_verdict(response)
    assert verdict == "superficial"
    assert confidence == "high"

def test_parse_verdict_missing_fields_returns_defaults():
    verdict, reason, confidence = sd.parse_verdict("")
    assert verdict == "unclear"
    assert reason == ""
    assert confidence == "low"


# --- main_with_payload: Edit ---

def test_edit_superficial_high_emits_warning_and_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: silences exception without fixing cause\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "def process():\n    broken()",
                "new_string": "def process():\n    try:\n        broken()\n    except:\n        pass",
            }
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert "[quality-guard]" in err.getvalue()
    assert "silences exception without fixing cause" in err.getvalue()
    raw = (tmp_path / ".claude" / "feedback" / "raw.md").read_text(encoding="utf-8")
    assert "[auto-detected]" in raw
    assert "src/app.py" in raw
    pending = (tmp_path / ".claude" / "quality" / "pending_review.txt").read_text(encoding="utf-8")
    assert pending == "1"


def test_edit_structural_high_produces_no_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_llm(_prompt):
        return "VERDICT: structural\nREASON: fixes root cause in logic\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "def broken(): return None",
                "new_string": "def fixed(): return compute()",
            }
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert not (tmp_path / ".claude" / "feedback" / "raw.md").exists()


def test_edit_superficial_medium_confidence_produces_no_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: might be suppression\nCONFIDENCE: medium"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "x = 1",
                "new_string": "x = 2",
            }
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert not (tmp_path / ".claude" / "feedback" / "raw.md").exists()


def test_edit_unclear_verdict_produces_no_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_llm(_prompt):
        return "VERDICT: unclear\nREASON: hard to say\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "x = 1",
                "new_string": "x = 2",
            }
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""


def test_edit_empty_old_string_skips_llm_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/app.py", "old_string": "", "new_string": "x = 1"}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert called == []


def test_edit_empty_new_string_skips_llm_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/app.py", "old_string": "x = 1", "new_string": ""}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert called == []


# --- main_with_payload: Write ---

def test_write_existing_file_superficial_high_emits_warning_and_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "app.py"
    existing.write_text("old content", encoding="utf-8")
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: hardcodes magic value\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": "x = 42"}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert "[quality-guard]" in err.getvalue()
    raw = (tmp_path / ".claude" / "feedback" / "raw.md").read_text(encoding="utf-8")
    assert "[auto-detected]" in raw
    pending = (tmp_path / ".claude" / "quality" / "pending_review.txt").read_text(encoding="utf-8")
    assert pending == "1"


def test_write_new_file_skips_llm_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    new_file = tmp_path / "new_module.py"
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {"file_path": str(new_file), "content": "x = 1"}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert called == []


def test_write_empty_content_skips_llm_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "app.py"
    existing.write_text("old", encoding="utf-8")
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": ""}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert called == []


def test_write_empty_file_path_skips_llm_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {"file_path": "", "content": "x = 1"}
        }, llm_fn=fake_llm)
    assert out.getvalue() == ""
    assert err.getvalue() == ""
    assert called == []


# --- NOT superficial prompt guidance ---

def test_edit_prompt_includes_not_superficial_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    captured = []
    def fake_llm(prompt):
        captured.append(prompt)
        return "VERDICT: structural\nREASON: ok\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "commands/feedback.md",
                "old_string": "<!-- checkpoint: <current UTC ISO8601> -->",
                "new_string": "<!-- checkpoint: 1970-01-01T00:00:00Z -->",
            }
        }, llm_fn=fake_llm)
    assert len(captured) == 1
    assert "NOT superficial" in captured[0]
    assert "sentinel value" in captured[0]


def test_write_prompt_includes_not_superficial_guidance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "config.md"
    existing.write_text("old content", encoding="utf-8")
    captured = []
    def fake_llm(prompt):
        captured.append(prompt)
        return "VERDICT: structural\nREASON: ok\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": "new content"}
        }, llm_fn=fake_llm)
    assert len(captured) == 1
    assert "NOT superficial" in captured[0]
    assert "sentinel value" in captured[0]


# --- Tailwind regression ---

def test_tailwind_grow_migration_does_not_block(tmp_path, monkeypatch):
    """Regression: Tailwind v4 flex-grow → grow migration must never produce blocking output."""
    monkeypatch.chdir(tmp_path)
    def fake_llm(_prompt):
        # Even if Haiku falsely judges this as superficial, no block must occur.
        return "VERDICT: superficial\nREASON: only renaming with no behavioral change\nCONFIDENCE: high"
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        sd.main_with_payload({
            "cwd": str(tmp_path),
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/components/Button.tsx",
                "old_string": '<div className="flex-grow" />',
                "new_string": '<div className="grow" />',
            }
        }, llm_fn=fake_llm)
    # Critical: stdout must be empty (no block JSON parsed by Claude Code).
    assert out.getvalue() == ""
    # Warning may be emitted; what matters is no block JSON.
    if err.getvalue():
        assert "decision" not in err.getvalue()


# --- edge cases ---

def test_non_dict_payload_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload("not a dict")
    assert f.getvalue() == ""

def test_unknown_tool_name_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({"tool_name": "Bash", "tool_input": {"command": "ls"}})
    assert f.getvalue() == ""

def test_missing_tool_input_produces_no_output():
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({"tool_name": "Edit"})
    assert f.getvalue() == ""
