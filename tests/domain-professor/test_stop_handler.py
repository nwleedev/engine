import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import stop_handler as sh


def test_main_skips_when_writing_context_set():
    with mock.patch.dict(os.environ, {"CLAUDE_WRITING_CONTEXT": "1"}):
        with mock.patch("stop_handler.detect_domains_from_transcript") as m:
            sh.main_with_payload({"transcript_path": "/fake/path", "cwd": "/cwd"})
    m.assert_not_called()


def test_main_skips_when_no_transcript_path():
    with mock.patch("stop_handler.detect_domains_from_transcript") as m:
        sh.main_with_payload({"cwd": "/cwd"})
    m.assert_not_called()


def test_main_skips_when_no_domains_detected(tmp_path):
    with mock.patch("stop_handler.detect_domains_from_transcript", return_value=[]), \
         mock.patch("stop_handler.generate_for_domains") as gen:
        sh.main_with_payload({"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path)})
    gen.assert_not_called()


def test_main_calls_generate_for_detected_domains(tmp_path):
    with mock.patch("stop_handler.detect_domains_from_transcript", return_value=["kubernetes"]), \
         mock.patch("stop_handler.find_project_root", return_value=str(tmp_path)), \
         mock.patch("stop_handler.generate_for_domains") as gen:
        sh.main_with_payload({"transcript_path": "/fake/t.jsonl", "cwd": str(tmp_path)})
    gen.assert_called_once_with(["kubernetes"], str(tmp_path))


def test_main_reads_stdin():
    payload = {"transcript_path": "/fake/t.jsonl", "cwd": "/tmp"}
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
         mock.patch("stop_handler.detect_domains_from_transcript", return_value=[]):
        sh.main()
