import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import inject_toc as it


def test_resolve_cwd_from_payload():
    assert it.resolve_cwd({"cwd": "/a/b"}) == "/a/b"


def test_resolve_cwd_from_env():
    with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/env/proj"}, clear=False):
        assert it.resolve_cwd({}) == "/env/proj"


def test_resolve_cwd_fallback_pwd():
    env_without = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env_without["PWD"] = "/pwd/proj"
    with mock.patch.dict(os.environ, env_without, clear=True):
        assert it.resolve_cwd({}) == "/pwd/proj"


def test_build_toc_context_empty_dir(tmp_path):
    textbooks_dir = tmp_path / ".claude" / "textbooks"
    assert it.build_toc_context(textbooks_dir) == ""


def test_build_toc_context_no_textbooks_dir(tmp_path):
    assert it.build_toc_context(tmp_path / "nonexistent") == ""


def test_build_toc_context_single_domain(tmp_path):
    textbooks_dir = tmp_path / ".claude" / "textbooks"
    domain_dir = textbooks_dir / "kubernetes"
    overview = domain_dir / "01-overview"
    overview.mkdir(parents=True)
    (domain_dir / "INDEX.md").write_text("# Kubernetes")
    (overview / "what-is-kubernetes.md").write_text("content")
    result = it.build_toc_context(textbooks_dir)
    assert "kubernetes" in result
    assert "1개 개념" in result
    assert "학습 텍스트북" in result


def test_build_toc_context_multiple_domains(tmp_path):
    textbooks_dir = tmp_path / ".claude" / "textbooks"
    for domain in ["docker", "kubernetes"]:
        d = textbooks_dir / domain / "01-overview"
        d.mkdir(parents=True)
        (textbooks_dir / domain / "INDEX.md").write_text(f"# {domain}")
        (d / f"what-is-{domain}.md").write_text("content")
    result = it.build_toc_context(textbooks_dir)
    assert "docker" in result
    assert "kubernetes" in result


def test_main_outputs_additional_context(tmp_path):
    textbooks_dir = tmp_path / ".claude" / "textbooks"
    domain_dir = textbooks_dir / "kubernetes" / "01-overview"
    domain_dir.mkdir(parents=True)
    (textbooks_dir / "kubernetes" / "INDEX.md").write_text("# K8s")
    (domain_dir / "what-is-kubernetes.md").write_text("content")
    payload = json.dumps({"session_id": "sess-new", "cwd": str(tmp_path)})
    captured = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)), \
         mock.patch("sys.stdout", captured), \
         mock.patch("inject_toc.find_project_root", return_value=str(tmp_path)):
        it.main()
    output = captured.getvalue().strip()
    assert output, "main() produced no output"
    data = json.loads(output)
    assert "additionalContext" in data.get("hookSpecificOutput", {})
    assert "kubernetes" in data["hookSpecificOutput"]["additionalContext"]


def test_main_silent_when_no_textbooks(tmp_path):
    payload = json.dumps({"session_id": "sess-new", "cwd": str(tmp_path)})
    captured = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(payload)), \
         mock.patch("sys.stdout", captured), \
         mock.patch("inject_toc.find_project_root", return_value=str(tmp_path)):
        it.main()
    assert captured.getvalue().strip() == ""
