import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory" / "scripts"


def load_extractor():
    spec = importlib.util.spec_from_file_location("evidence_extractor", SCRIPTS / "evidence_extractor.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extracts_files_commands_failures_and_sources():
    extractor = load_extractor()
    delta = [
        {"role": "assistant", "text": "Run: `python -m pytest tests/foo.py -q`\nFAIL tests/foo.py::test_bar"},
        {"role": "assistant", "text": "Edited plugins/codex-session-memory/scripts/policy.py"},
        {"role": "assistant", "text": "Source: https://developers.openai.com/codex/hooks"},
    ]
    evidence = extractor.extract_evidence(delta)
    assert "plugins/codex-session-memory/scripts/policy.py" in evidence["files"]
    assert "python -m pytest tests/foo.py -q" in evidence["commands"]
    assert "FAIL tests/foo.py::test_bar" in evidence["failures"]
    assert "https://developers.openai.com/codex/hooks" in evidence["sources"]
