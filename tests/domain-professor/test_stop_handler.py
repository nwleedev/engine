import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import domain_professor_stop as sh


def test_main_skips_when_writing_context_set(tmp_path):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch.dict(os.environ, {"CLAUDE_WRITING_CONTEXT": "1"}), \
         mock.patch.object(sh, "detect_domains_free_form") as m, \
         mock.patch.object(sh, "find_project_root", return_value=str(tmp_path)):
        sh.main_with_payload(payload)
    m.assert_not_called()


def test_main_skips_when_no_transcript(tmp_path):
    with mock.patch.object(sh, "detect_domains_free_form") as m:
        sh.main_with_payload({"cwd": str(tmp_path), "session_id": "s1"})
    m.assert_not_called()


def test_main_skips_when_flag_inactive(tmp_path):
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch.object(sh, "detect_domains_free_form") as m, \
         mock.patch.object(sh, "find_project_root", return_value=str(tmp_path)):
        sh.main_with_payload(payload)
    m.assert_not_called()


def test_main_skips_when_no_domains(tmp_path):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch.object(sh, "parse_transcript", return_value=[]), \
         mock.patch.object(sh, "detect_domains_free_form", return_value=[]), \
         mock.patch.object(sh, "generate_for_domains") as gen, \
         mock.patch.object(sh, "find_project_root", return_value=str(tmp_path)):
        sh.main_with_payload(payload)
    gen.assert_not_called()


def test_main_generates_when_flag_active_and_domains_detected(tmp_path):
    flag = tmp_path / ".claude" / "sessions" / "s1" / ".professor-active"
    flag.parent.mkdir(parents=True)
    flag.touch()
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path), "session_id": "s1"}
    with mock.patch.object(sh, "parse_transcript", return_value=[{"role": "user", "text": "k8s"}]), \
         mock.patch.object(sh, "detect_domains_free_form", return_value=["kubernetes"]), \
         mock.patch.object(sh, "generate_for_domains") as gen, \
         mock.patch.object(sh, "find_project_root", return_value=str(tmp_path)):
        sh.main_with_payload(payload)
    gen.assert_called_once_with(["kubernetes"], str(tmp_path))


def test_main_reads_stdin():
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": "/tmp", "session_id": "s1"}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch.object(sh, "parse_transcript", return_value=[]), \
         mock.patch.object(sh, "detect_domains_free_form", return_value=[]):
        sh.main()
