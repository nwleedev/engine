import io
import json
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
HOOKS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/hooks"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import user_prompt_submit as ups


def test_main_silent_when_inactive(tmp_path, capsys):
    payload = {"session_id": "s1", "cwd": str(tmp_path)}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch("inject_toc.find_project_root", return_value=str(tmp_path)):
        ups.main()
    assert capsys.readouterr().out.strip() == ""


def test_main_injects_skill_when_active(tmp_path, capsys):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"session_id": "s1", "cwd": str(tmp_path)}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch("inject_toc.find_project_root", return_value=str(tmp_path)), \
         mock.patch("user_prompt_submit.read_skill_content", return_value="# Professor\n"):
        ups.main()
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "Professor" in out["hookSpecificOutput"]["additionalContext"]


def test_main_silent_when_skill_empty(tmp_path, capsys):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"session_id": "s1", "cwd": str(tmp_path)}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch("inject_toc.find_project_root", return_value=str(tmp_path)), \
         mock.patch("user_prompt_submit.read_skill_content", return_value=""):
        ups.main()
    assert capsys.readouterr().out.strip() == ""


def test_main_silent_on_bad_stdin(capsys):
    with mock.patch("sys.stdin", io.StringIO("not json")):
        ups.main()
    assert capsys.readouterr().out.strip() == ""
