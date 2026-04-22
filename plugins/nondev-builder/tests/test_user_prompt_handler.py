import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from nondev_io import upsert_domain
from user_prompt_handler import match_domain, main_with_payload


def _make_domain(task_name: str, ko: list[str], en: list[str]) -> dict:
    return {
        "task_name": task_name,
        "display_name": task_name,
        "command": f"/{task_name}",
        "keywords": {"ko": ko, "en": en},
    }


def test_match_korean_keyword(tmp_path):
    domains = [_make_domain("market-research", ["시장 규모", "경쟁사"], ["market size"])]
    assert match_domain("경쟁사 분석 해줘", domains) is not None


def test_match_english_keyword(tmp_path):
    domains = [_make_domain("market-research", ["시장"], ["market size", "competitor"])]
    assert match_domain("what is the market size?", domains) is not None


def test_no_match_returns_none(tmp_path):
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
