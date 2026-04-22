import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "plugins/nondev-builder/scripts"))
from nondev_io import upsert_domain
from session_start_handler import build_context, main_with_payload


def test_no_index_returns_setup_prompt(tmp_path):
    result = build_context(str(tmp_path))
    assert "No nondev domain configured" in result
    assert "/nondev-setup" in result


def test_empty_domains_returns_setup_prompt(tmp_path):
    # Create index.json with empty domains list
    index_path = tmp_path / ".claude" / "nondev"
    index_path.mkdir(parents=True)
    (index_path / "index.json").write_text(
        '{"version": "1", "updated": "2026-04-22", "domains": []}', encoding="utf-8"
    )
    result = build_context(str(tmp_path))
    assert "No nondev domain configured" in result


def test_single_domain_returns_command(tmp_path):
    upsert_domain(str(tmp_path), {
        "task_name": "market-research",
        "display_name": "Market Research",
        "command": "/market-research",
        "keywords": {"ko": [], "en": []},
    })
    result = build_context(str(tmp_path))
    assert "market-research" in result
    assert "/market-research" in result


def test_multiple_domains_listed(tmp_path):
    for name in ["market-research", "stock-analysis"]:
        upsert_domain(str(tmp_path), {
            "task_name": name,
            "display_name": name,
            "command": f"/{name}",
            "keywords": {"ko": [], "en": []},
        })
    result = build_context(str(tmp_path))
    assert "market-research" in result
    assert "stock-analysis" in result


def test_malformed_entry_without_task_name_is_detected(tmp_path):
    # Manually write an index with one bad entry and one good entry
    index_path = tmp_path / ".claude" / "nondev"
    index_path.mkdir(parents=True)
    (index_path / "index.json").write_text(
        json.dumps({
            "version": "1",
            "updated": "2026-04-22",
            "domains": [
                {"display_name": "broken entry"},  # missing task_name
                {"task_name": "stock-analysis", "display_name": "Stock Analysis", "command": "/stock-analysis", "keywords": {"ko": [], "en": []}},
            ],
        }),
        encoding="utf-8",
    )
    result = build_context(str(tmp_path))
    # Should detect corruption and prompt user to rebuild
    assert "corrupted" in result.lower()
    assert "/nondev-setup" in result


def test_non_dict_domain_entry_is_detected(tmp_path):
    # Manually write an index with a non-dict entry
    index_path = tmp_path / ".claude" / "nondev"
    index_path.mkdir(parents=True)
    (index_path / "index.json").write_text(
        json.dumps({
            "version": "1",
            "updated": "2026-04-22",
            "domains": [
                "invalid string entry",  # not a dict
            ],
        }),
        encoding="utf-8",
    )
    result = build_context(str(tmp_path))
    assert "corrupted" in result.lower()
    assert "/nondev-setup" in result


def test_main_with_payload_emits_hook_json(tmp_path, capsys):
    upsert_domain(str(tmp_path), {
        "task_name": "test-domain",
        "display_name": "Test Domain",
        "command": "/test",
        "keywords": {"ko": [], "en": []},
    })
    main_with_payload({"cwd": str(tmp_path)})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "additionalContext" in output["hookSpecificOutput"]
    assert "test-domain" in output["hookSpecificOutput"]["additionalContext"]


def test_main_with_payload_silent_on_non_dict():
    # Should return without printing
    import io
    from contextlib import redirect_stdout
    f = io.StringIO()
    with redirect_stdout(f):
        main_with_payload("not a dict")
    assert f.getvalue() == ""
