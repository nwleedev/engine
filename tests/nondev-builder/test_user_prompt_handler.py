import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "plugins/nondev-builder/scripts"))
from nondev_io import upsert_domain, read_index, write_rubric
from user_prompt_handler import match_domain, main_with_payload, build_rubric_context


def _make_domain(task_name: str, ko: list[str], en: list[str]) -> dict:
    return {
        "task_name": task_name,
        "display_name": task_name,
        "command": f"/{task_name}",
        "keywords": {"ko": ko, "en": en},
    }


def test_match_korean_keyword():
    domains = [_make_domain("market-research", ["시장 규모", "경쟁사"], ["market size"])]
    assert match_domain("경쟁사 분석 해줘", domains) is not None


def test_match_english_keyword():
    domains = [_make_domain("market-research", ["시장"], ["market size", "competitor"])]
    assert match_domain("what is the market size?", domains) is not None


def test_no_match_returns_none():
    domains = [_make_domain("market-research", ["시장"], ["market"])]
    assert match_domain("오늘 날씨가 좋네요", domains) is None


def test_case_insensitive_match():
    domains = [_make_domain("market-research", [], ["Market Size"])]
    assert match_domain("tell me about MARKET SIZE trends", domains) is not None


def test_first_domain_wins_on_multi_match():
    domains = [
        _make_domain("market-research", [], ["analysis"]),
        _make_domain("stock-analysis", [], ["analysis"]),
    ]
    result = match_domain("do an analysis", domains)
    assert result["task_name"] == "market-research"


def test_main_with_payload_emits_suggestion(tmp_path, capsys):
    upsert_domain(str(tmp_path), _make_domain("market-research", ["시장"], ["market"]))
    main_with_payload({"prompt": "시장 조사 해줘", "cwd": str(tmp_path)})
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "market-research" in output["hookSpecificOutput"]["additionalContext"]


def test_main_with_payload_silent_on_no_match(tmp_path, capsys):
    upsert_domain(str(tmp_path), _make_domain("market-research", ["시장"], ["market"]))
    main_with_payload({"prompt": "날씨 알려줘", "cwd": str(tmp_path)})
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_with_payload_silent_on_no_index(tmp_path, capsys):
    main_with_payload({"prompt": "시장 규모", "cwd": str(tmp_path)})
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_with_payload_silent_on_non_dict(capsys):
    main_with_payload("not a dict")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_read_index_called_exactly_once(tmp_path):
    upsert_domain(str(tmp_path), _make_domain("market-research", ["시장"], ["market"]))
    upsert_domain(str(tmp_path), _make_domain("stock-analysis", ["주식"], ["stock"]))
    with patch("user_prompt_handler.read_index", wraps=read_index) as mock_read:
        main_with_payload({"prompt": "시장 분석", "cwd": str(tmp_path)})
        assert mock_read.call_count == 1


def test_build_rubric_context_empty():
    assert build_rubric_context([]) == ""


def test_build_rubric_context_single():
    result = build_rubric_context([("market-research", "# Rubric\n## Violations\n| id |")])
    assert "market-research" in result
    assert "Apply the following nondev quality rubrics" in result


def test_build_rubric_context_multiple():
    rubrics = [
        ("market-research", "# Market Rubric"),
        ("stock-analysis", "# Stock Rubric"),
    ]
    result = build_rubric_context(rubrics)
    assert "market-research" in result
    assert "stock-analysis" in result
