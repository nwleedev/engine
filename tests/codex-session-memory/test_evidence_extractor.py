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


def test_ignores_partial_file_matches_inside_unsupported_extensions():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": "Ignore __pycache__/evidence_extractor.cpython-312.pyc and archive.mdx, edit docs/spec.md.",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert "__pycache__/evidence_extractor.cpython-312.py" not in evidence["files"]
    assert "archive.md" not in evidence["files"]
    assert "docs/spec.md" in evidence["files"]


def test_caps_commands_sources_and_failures():
    extractor = load_extractor()
    commands = "\n".join(f"python script_{index}.py" for index in range(35))
    sources = " ".join(f"https://example.com/{index}" for index in range(35))
    failures = "\n".join(f"FAIL tests/test_{index}.py::test_case" for index in range(25))
    evidence = extractor.extract_evidence([{"role": "assistant", "text": f"{commands}\n{sources}\n{failures}"}])
    assert evidence["commands"] == [f"python script_{index}.py" for index in range(30)]
    assert evidence["sources"] == [f"https://example.com/{index}" for index in range(30)]
    assert evidence["failures"] == [f"FAIL tests/test_{index}.py::test_case" for index in range(20)]


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


def test_extracts_common_codex_transcript_commands_from_fences_and_plain_lines():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": "Run:\n```bash\nrg extract_evidence\nsed -n '1,40p' file.py\ngh pr view 1\n"
            "node scripts/check.mjs\nuv run ruff check\nruff format .\nmypy package\n```\n$ rg TODO\nsed -n '1,20p' README.md",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert "rg extract_evidence" in evidence["commands"]
    assert "sed -n '1,40p' file.py" in evidence["commands"]
    assert "gh pr view 1" in evidence["commands"]
    assert "node scripts/check.mjs" in evidence["commands"]
    assert "uv run ruff check" in evidence["commands"]
    assert "ruff format ." in evidence["commands"]
    assert "mypy package" in evidence["commands"]
    assert "rg TODO" in evidence["commands"]
    assert "sed -n '1,20p' README.md" in evidence["commands"]


def test_extracts_fenced_commands_without_language_marker():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": "Run:\n```\nnpm test\npython -m pytest tests/foo.py -q\n```",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert "npm test" in evidence["commands"]
    assert "python -m pytest tests/foo.py -q" in evidence["commands"]


def test_extracts_plain_transcript_command_lines():
    extractor = load_extractor()
    delta = [
        {"role": "assistant", "text": "python -m pytest tests/foo.py -q\n$ git status --short"},
    ]
    evidence = extractor.extract_evidence(delta)
    assert "python -m pytest tests/foo.py -q" in evidence["commands"]
    assert "git status --short" in evidence["commands"]


def test_inline_file_like_values_are_not_commands():
    extractor = load_extractor()
    delta = [
        {
            "role": "assistant",
            "text": "Check `.gitignore`, `plugins/digital.py`, `npm-package.json`, then run `npm test`.",
        }
    ]
    evidence = extractor.extract_evidence(delta)
    assert ".gitignore" not in evidence["commands"]
    assert "plugins/digital.py" not in evidence["commands"]
    assert "npm-package.json" not in evidence["commands"]
    assert "npm test" in evidence["commands"]


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
