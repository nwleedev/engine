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


def test_keeps_url_internal_file_paths_out_of_files():
    extractor = load_extractor()
    delta = [
        {"role": "assistant", "text": "Source: https://example.com/docs/config.json"},
        {"role": "assistant", "text": "Edited local/config.json"},
    ]
    evidence = extractor.extract_evidence(delta)
    assert "https://example.com/docs/config.json" in evidence["sources"]
    assert "local/config.json" in evidence["files"]
    assert all("example.com" not in file for file in evidence["files"])


def test_preserves_order_and_removes_duplicates():
    extractor = load_extractor()
    delta = [
        {"role": "assistant", "text": "Edited first.py then second.py and first.py"},
        {"role": "assistant", "text": "Run: `python first.py` and `python first.py` then `git status`"},
    ]
    evidence = extractor.extract_evidence(delta)
    assert evidence["files"] == ["first.py", "second.py"]
    assert evidence["commands"] == ["python first.py", "git status"]


def test_caps_files_to_forty_items():
    extractor = load_extractor()
    delta = [{"role": "assistant", "text": " ".join(f"file_{index}.py" for index in range(45))}]
    evidence = extractor.extract_evidence(delta)
    assert evidence["files"] == [f"file_{index}.py" for index in range(40)]


def test_extracts_fenced_shell_commands_without_language_marker():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": "Run:\n```bash\npython -m pytest tests/foo.py -q\ngit status --short\n```",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert "python -m pytest tests/foo.py -q" in evidence["commands"]
    assert "git status --short" in evidence["commands"]
    assert "bash" not in evidence["commands"]


def test_extracts_plain_transcript_command_lines():
    extractor = load_extractor()
    delta = [
        {"role": "assistant", "text": "python -m pytest tests/foo.py -q\n$ git status --short"},
    ]
    evidence = extractor.extract_evidence(delta)
    assert "python -m pytest tests/foo.py -q" in evidence["commands"]
    assert "git status --short" in evidence["commands"]


def test_trims_common_trailing_url_punctuation():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": 'Sources: https://example.com/a.json`, https://example.com/b.md"; '
            "https://example.com/c.toml] https://example.com/d.yaml} "
            "https://example.com/e.yml> https://example.com/f.ts: https://example.com/g.js;",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert evidence["sources"] == [
        "https://example.com/a.json",
        "https://example.com/b.md",
        "https://example.com/c.toml",
        "https://example.com/d.yaml",
        "https://example.com/e.yml",
        "https://example.com/f.ts",
        "https://example.com/g.js",
    ]
