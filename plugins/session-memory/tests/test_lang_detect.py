import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import lang_detect


def test_from_settings_json(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"env": {"SESSION_MEMORY_LANG": "ko"}}), encoding="utf-8"
    )
    assert lang_detect.detect(str(tmp_path)) == "ko"


def test_settings_local_overrides_settings(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"env": {"SESSION_MEMORY_LANG": "en"}}), encoding="utf-8"
    )
    (tmp_path / ".claude" / "settings.local.json").write_text(
        json.dumps({"env": {"SESSION_MEMORY_LANG": "ko"}}), encoding="utf-8"
    )
    assert lang_detect.detect(str(tmp_path)) == "ko"


def test_from_os_lang_env(tmp_path, monkeypatch):
    monkeypatch.setenv("LANG", "ko_KR.UTF-8")
    assert lang_detect.detect(str(tmp_path)) == "ko"


def test_settings_takes_priority_over_os(tmp_path, monkeypatch):
    monkeypatch.setenv("LANG", "ko_KR.UTF-8")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps({"env": {"SESSION_MEMORY_LANG": "en"}}), encoding="utf-8"
    )
    assert lang_detect.detect(str(tmp_path)) == "en"


def test_default_en(tmp_path, monkeypatch):
    monkeypatch.delenv("LANG", raising=False)
    assert lang_detect.detect(str(tmp_path)) == "en"


def test_unsupported_lang_falls_back_to_en(tmp_path, monkeypatch):
    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    assert lang_detect.detect(str(tmp_path)) == "en"
