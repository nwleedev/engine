import importlib.util
import json
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_parser():
    spec = importlib.util.spec_from_file_location("jsonl_parser", SCRIPTS / "jsonl_parser.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extract_delta_includes_function_call_output_as_tool_text(tmp_path):
    parser = load_parser()
    transcript = tmp_path / "rollout.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "I will inspect files."}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call_output",
                            "call_id": "call-1",
                            "output": "pytest output\nFAIL tests/example.py::test_case",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    delta, new_offset = parser.extract_delta(str(transcript), 0)

    assert delta == [
        {"role": "assistant", "text": "I will inspect files."},
        {"role": "tool", "text": "pytest output\nFAIL tests/example.py::test_case"},
    ]
    assert new_offset == transcript.stat().st_size
