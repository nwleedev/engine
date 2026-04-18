import json
import os
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/domain-professor/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_textbook as gt


def test_find_project_root_uses_git(tmp_path):
    with mock.patch("subprocess.run") as m:
        m.return_value = mock.Mock(returncode=0, stdout=str(tmp_path) + "\n")
        result = gt.find_project_root(str(tmp_path))
    assert result == str(tmp_path)


def test_find_project_root_falls_back_to_claude_dir(tmp_path):
    (tmp_path / ".claude").mkdir()
    sub = tmp_path / "sub"
    sub.mkdir()
    with mock.patch("subprocess.run") as m:
        m.return_value = mock.Mock(returncode=1, stdout="")
        result = gt.find_project_root(str(sub))
    assert result == str(tmp_path)


def test_call_claude_returns_result():
    fake_output = json.dumps({"result": "# Test\n\nContent here"})
    with mock.patch("subprocess.run") as m:
        m.return_value = mock.Mock(returncode=0, stdout=fake_output)
        result = gt.call_claude("test prompt")
    assert result == "# Test\n\nContent here"


def test_call_claude_returns_empty_on_failure():
    with mock.patch("subprocess.run") as m:
        m.return_value = mock.Mock(returncode=1, stdout="")
        result = gt.call_claude("test prompt")
    assert result == ""


def test_ensure_index_creates_file(tmp_path):
    domain_dir = tmp_path / "kubernetes"
    domain_dir.mkdir()
    gt.ensure_index(domain_dir, "kubernetes")
    index = domain_dir / "INDEX.md"
    assert index.exists()
    content = index.read_text()
    assert "Kubernetes" in content
    assert "01-overview" in content


def test_ensure_index_does_not_overwrite(tmp_path):
    domain_dir = tmp_path / "kubernetes"
    domain_dir.mkdir()
    index = domain_dir / "INDEX.md"
    index.write_text("existing content")
    gt.ensure_index(domain_dir, "kubernetes")
    assert index.read_text() == "existing content"


def test_update_index_appends_link(tmp_path):
    domain_dir = tmp_path / "kubernetes"
    domain_dir.mkdir()
    index = domain_dir / "INDEX.md"
    index.write_text("# Kubernetes Textbook\n\n## Overview\n\n## Core Concepts\n\n## Advanced\n")
    gt.update_index(domain_dir, "02-core-concepts/pods.md", "Pods", "02-core-concepts")
    content = index.read_text()
    assert "[Pods](./02-core-concepts/pods.md)" in content


def test_update_index_no_duplicate(tmp_path):
    domain_dir = tmp_path / "kubernetes"
    domain_dir.mkdir()
    index = domain_dir / "INDEX.md"
    index.write_text("# Kubernetes Textbook\n\n## Core Concepts\n- [Pods](./02-core-concepts/pods.md)\n")
    gt.update_index(domain_dir, "02-core-concepts/pods.md", "Pods", "02-core-concepts")
    content = index.read_text()
    assert content.count("[Pods]") == 1


def test_generate_file_creates_md(tmp_path):
    fake_content = "---\nstage: core-concepts\n---\n\n# Pods\n\nContent"
    with mock.patch("generate_textbook.call_claude", return_value=fake_content):
        result = gt.generate_file("kubernetes", "02-core-concepts", "pods", tmp_path, "skill")
    assert result is True
    assert (tmp_path / "02-core-concepts" / "pods.md").exists()


def test_generate_file_skips_existing(tmp_path):
    stage_dir = tmp_path / "02-core-concepts"
    stage_dir.mkdir()
    (stage_dir / "pods.md").write_text("existing")
    with mock.patch("generate_textbook.call_claude") as m:
        result = gt.generate_file("kubernetes", "02-core-concepts", "pods", tmp_path, "skill")
    assert result is False
    m.assert_not_called()


def test_get_existing_concepts(tmp_path):
    (tmp_path / "02-core-concepts").mkdir()
    (tmp_path / "02-core-concepts" / "pods.md").write_text("")
    (tmp_path / "INDEX.md").write_text("")
    concepts = gt.get_existing_concepts(tmp_path)
    assert "pods" in concepts
    assert "INDEX" not in concepts


def test_generate_file_injects_language_instruction(tmp_path):
    fake_content = "---\nstage: 02-core-concepts\n---\n\n# Pods\n\nContent"
    captured = {}
    def capture(prompt):
        captured["prompt"] = prompt
        return fake_content
    with mock.patch.dict("os.environ", {"DOMAIN_PROFESSOR_LANGUAGE": "Korean"}):
        with mock.patch("generate_textbook.call_claude", side_effect=capture):
            gt.generate_file("kubernetes", "02-core-concepts", "pods", tmp_path, "skill")
    assert "Korean" in captured["prompt"]


def test_generate_file_defaults_to_english(tmp_path):
    fake_content = "---\nstage: 02-core-concepts\n---\n\n# Pods\n\nContent"
    captured = {}
    def capture(prompt):
        captured["prompt"] = prompt
        return fake_content
    env = {k: v for k, v in os.environ.items() if k != "DOMAIN_PROFESSOR_LANGUAGE"}
    with mock.patch.dict("os.environ", env, clear=True):
        with mock.patch("generate_textbook.call_claude", side_effect=capture):
            gt.generate_file("kubernetes", "02-core-concepts", "pods", tmp_path, "skill")
    assert "English" in captured["prompt"]
