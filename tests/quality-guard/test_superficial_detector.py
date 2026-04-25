# tests/quality-guard/test_superficial_detector.py
import io
import json
import sys
from contextlib import redirect_stdout
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


# --- should_block ---

def test_should_block_superficial_high_returns_true():
    assert sd.should_block("superficial", "high") is True

def test_should_block_superficial_medium_returns_false():
    assert sd.should_block("superficial", "medium") is False

def test_should_block_superficial_low_returns_false():
    assert sd.should_block("superficial", "low") is False

def test_should_block_structural_high_returns_false():
    assert sd.should_block("structural", "high") is False

def test_should_block_unclear_high_returns_false():
    assert sd.should_block("unclear", "high") is False


# --- main_with_payload: Edit ---

def test_edit_superficial_high_outputs_block():
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: silences exception without fixing cause\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "def process():\n    broken()",
                "new_string": "def process():\n    try:\n        broken()\n    except:\n        pass",
            }
        }, llm_fn=fake_llm)
    output = json.loads(f.getvalue())
    assert output["decision"] == "block"
    assert "[quality-guard]" in output["reason"]
    assert "silences exception without fixing cause" in output["reason"]

def test_edit_structural_high_produces_no_output():
    def fake_llm(_prompt):
        return "VERDICT: structural\nREASON: fixes root cause in logic\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "def broken(): return None",
                "new_string": "def fixed(): return compute()",
            }
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""

def test_edit_superficial_medium_confidence_produces_no_output():
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: might be suppression\nCONFIDENCE: medium"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "x = 1",
                "new_string": "x = 2",
            }
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""

def test_edit_unclear_verdict_produces_no_output():
    def fake_llm(_prompt):
        return "VERDICT: unclear\nREASON: hard to say\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "src/app.py",
                "old_string": "x = 1",
                "new_string": "x = 2",
            }
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""

def test_edit_empty_old_string_skips_llm_call():
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/app.py", "old_string": "", "new_string": "x = 1"}
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""
    assert called == []

def test_edit_empty_new_string_skips_llm_call():
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/app.py", "old_string": "x = 1", "new_string": ""}
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""
    assert called == []


# --- main_with_payload: Write ---

def test_write_existing_file_superficial_high_outputs_block(tmp_path):
    existing = tmp_path / "app.py"
    existing.write_text("old content", encoding="utf-8")
    def fake_llm(_prompt):
        return "VERDICT: superficial\nREASON: hardcodes magic value\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": "x = 42"}
        }, llm_fn=fake_llm)
    output = json.loads(f.getvalue())
    assert output["decision"] == "block"

def test_write_new_file_skips_llm_call(tmp_path):
    new_file = tmp_path / "new_module.py"
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Write",
            "tool_input": {"file_path": str(new_file), "content": "x = 1"}
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""
    assert called == []

def test_write_empty_content_skips_llm_call(tmp_path):
    existing = tmp_path / "app.py"
    existing.write_text("old", encoding="utf-8")
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": ""}
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""
    assert called == []

def test_write_empty_file_path_skips_llm_call():
    called = []
    def fake_llm(_prompt):
        called.append(True)
        return "VERDICT: superficial\nREASON: bad\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Write",
            "tool_input": {"file_path": "", "content": "x = 1"}
        }, llm_fn=fake_llm)
    assert f.getvalue() == ""
    assert called == []


# --- NOT superficial prompt guidance ---

def test_edit_prompt_includes_not_superficial_guidance():
    captured = []
    def fake_llm(prompt):
        captured.append(prompt)
        return "VERDICT: structural\nREASON: ok\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
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

def test_write_prompt_includes_not_superficial_guidance(tmp_path):
    existing = tmp_path / "config.md"
    existing.write_text("old content", encoding="utf-8")
    captured = []
    def fake_llm(prompt):
        captured.append(prompt)
        return "VERDICT: structural\nREASON: ok\nCONFIDENCE: high"
    f = io.StringIO()
    with redirect_stdout(f):
        sd.main_with_payload({
            "tool_name": "Write",
            "tool_input": {"file_path": str(existing), "content": "new content"}
        }, llm_fn=fake_llm)
    assert len(captured) == 1
    assert "NOT superficial" in captured[0]
    assert "sentinel value" in captured[0]


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
