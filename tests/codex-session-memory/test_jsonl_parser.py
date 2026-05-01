from pathlib import Path
import jsonl_parser as jp

FIXTURE = Path(__file__).parent / "fixtures" / "sample_rollout.jsonl"


def test_extract_delta_from_offset_zero():
    msgs, new_offset = jp.extract_delta(str(FIXTURE), 0)
    assert [(m["role"], m["text"]) for m in msgs] == [
        ("user", "Add tests for auth"),
        ("assistant", "Adding tests now."),
    ]
    assert new_offset == FIXTURE.stat().st_size


def test_extract_delta_skips_already_processed():
    full_size = FIXTURE.stat().st_size
    msgs, new_offset = jp.extract_delta(str(FIXTURE), full_size)
    assert msgs == []
    assert new_offset == full_size


def test_extract_delta_partial_offset():
    text = FIXTURE.read_bytes()
    target = b'"role":"user"'
    pos = text.find(target)
    line_start = text.rfind(b"\n", 0, pos) + 1
    msgs, new_offset = jp.extract_delta(str(FIXTURE), line_start)
    assert [(m["role"], m["text"]) for m in msgs] == [
        ("user", "Add tests for auth"),
        ("assistant", "Adding tests now."),
    ]
    assert new_offset == FIXTURE.stat().st_size


def test_extract_delta_handles_malformed_lines(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text(
        '{"type":"response_item","payload":{"role":"user","content":[{"type":"input_text","text":"ok"}]}}\n'
        'not json at all\n'
        '{"type":"response_item","payload":{"role":"assistant","content":[{"type":"output_text","text":"hi"}]}}\n'
    )
    msgs, _ = jp.extract_delta(str(p), 0)
    assert [(m["role"], m["text"]) for m in msgs] == [("user", "ok"), ("assistant", "hi")]
