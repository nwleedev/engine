import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from nondev_io import read_index, upsert_domain, write_rubric
from stop_handler import build_evaluation_prompt, main_with_payload


def _make_domain(task_name: str) -> dict:
    return {
        "task_name": task_name,
        "display_name": task_name,
        "command": f"/{task_name}",
        "keywords": {"ko": [], "en": []},
    }


def test_build_evaluation_prompt_empty():
    assert build_evaluation_prompt([]) == ""


def test_build_evaluation_prompt_single():
    result = build_evaluation_prompt([("market-research", "# Rubric\n## Violations\n| id |")])
    assert "market-research" in result
    assert "evaluate your most recent response" in result
    assert "1 revision only" in result


def test_build_evaluation_prompt_multiple():
    rubrics = [
        ("market-research", "# Market Rubric"),
        ("stock-analysis", "# Stock Rubric"),
    ]
    result = build_evaluation_prompt(rubrics)
    assert "market-research" in result
    assert "stock-analysis" in result


def test_silent_when_no_index(tmp_path, capsys):
    main_with_payload({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_silent_when_no_rubrics(tmp_path, capsys):
    upsert_domain(str(tmp_path), _make_domain("market-research"))
    # No rubric.md written — should be silent
    main_with_payload({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_silent_when_domains_list_empty(tmp_path, capsys):
    # Write index.json with empty domains list
    import json as _json
    index_path = tmp_path / ".claude" / "nondev"
    index_path.mkdir(parents=True)
    (index_path / "index.json").write_text(
        _json.dumps({"version": "1", "updated": "2026-04-22", "domains": []}),
        encoding="utf-8",
    )
    main_with_payload({"cwd": str(tmp_path)})
    assert capsys.readouterr().out == ""


def test_emits_json_when_rubric_present(tmp_path, capsys):
    upsert_domain(str(tmp_path), _make_domain("market-research"))
    write_rubric(str(tmp_path), "market-research", "# Rubric\n## Violation Criteria\n| id | Type |")
    main_with_payload({"cwd": str(tmp_path)})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "market-research" in output["hookSpecificOutput"]["additionalContext"]


def test_skips_domain_without_task_name(tmp_path, capsys):
    # Manually write a malformed index entry
    import json as _json
    index_path = tmp_path / ".claude" / "nondev"
    index_path.mkdir(parents=True)
    (index_path / "index.json").write_text(
        _json.dumps({
            "version": "1",
            "updated": "2026-04-22",
            "domains": [
                {"display_name": "broken"},  # no task_name
                {"task_name": "stock-analysis", "display_name": "Stock", "command": "/stock-analysis", "keywords": {"ko": [], "en": []}},
            ],
        }),
        encoding="utf-8",
    )
    write_rubric(str(tmp_path), "stock-analysis", "# Rubric")
    main_with_payload({"cwd": str(tmp_path)})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "stock-analysis" in output["hookSpecificOutput"]["additionalContext"]


def test_skips_missing_rubric_silently(tmp_path, capsys):
    upsert_domain(str(tmp_path), _make_domain("market-research"))
    upsert_domain(str(tmp_path), _make_domain("stock-analysis"))
    # Only stock-analysis has a rubric
    write_rubric(str(tmp_path), "stock-analysis", "# Stock Rubric")
    main_with_payload({"cwd": str(tmp_path)})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    # stock-analysis is present, market-research is absent (no rubric)
    assert "stock-analysis" in output["hookSpecificOutput"]["additionalContext"]
    assert "market-research" not in output["hookSpecificOutput"]["additionalContext"]


def test_read_index_called_once(tmp_path):
    upsert_domain(str(tmp_path), _make_domain("market-research"))
    upsert_domain(str(tmp_path), _make_domain("stock-analysis"))
    write_rubric(str(tmp_path), "market-research", "# Rubric A")
    write_rubric(str(tmp_path), "stock-analysis", "# Rubric B")
    with patch("stop_handler.read_index", wraps=read_index) as mock_read:
        main_with_payload({"cwd": str(tmp_path)})
        assert mock_read.call_count == 1


def test_silent_on_non_dict_payload(capsys):
    main_with_payload("not a dict")
    assert capsys.readouterr().out == ""
