import io
import json
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import toggle_state as ts


def test_toggle_activates_when_inactive(tmp_path):
    payload = {"cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch("toggle_state.find_project_root", return_value=str(tmp_path)):
        result = ts.main_with_payload(payload)
    assert result == "active"
    assert (tmp_path / ".claude" / "sessions" / "s1" / ".professor-active").exists()


def test_toggle_deactivates_when_active(tmp_path):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch("toggle_state.find_project_root", return_value=str(tmp_path)):
        result = ts.main_with_payload(payload)
    assert result == "inactive"
    assert not flag.exists()


def test_toggle_returns_inactive_when_no_session_info(tmp_path):
    payload = {"cwd": str(tmp_path)}  # no session_id, no transcript_path
    with mock.patch("toggle_state.find_project_root", return_value=str(tmp_path)):
        result = ts.main_with_payload(payload)
    assert result == "inactive"


def test_toggle_returns_inactive_when_empty_payload():
    result = ts.main_with_payload({})
    assert result == "inactive"


def test_main_prints_result(tmp_path, capsys):
    payload = {"cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch("toggle_state.find_project_root", return_value=str(tmp_path)):
        ts.main()
    assert capsys.readouterr().out.strip() == "active"
