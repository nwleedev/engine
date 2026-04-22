import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from project_reader import read_project_files


def test_reads_readme(tmp_path):
    (tmp_path / "README.md").write_text("# My Project\nA tool for market research.")
    result = read_project_files(str(tmp_path))
    assert "README.md" in result
    assert "market research" in result


def test_reads_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Project Rules\nLanguage: English")
    result = read_project_files(str(tmp_path))
    assert "CLAUDE.md" in result
    assert "Project Rules" in result


def test_missing_files_returns_empty_string(tmp_path):
    result = read_project_files(str(tmp_path))
    assert result == ""


def test_missing_readme_still_reads_claude_md(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Rules\nUse Python.")
    result = read_project_files(str(tmp_path))
    assert "CLAUDE.md" in result
    assert "README.md" not in result


def test_truncates_large_readme(tmp_path):
    (tmp_path / "README.md").write_text("A" * 5000)
    result = read_project_files(str(tmp_path))
    assert len(result) < 5000


def test_git_log_included_when_git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    (tmp_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial commit"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    result = read_project_files(str(tmp_path))
    assert "initial commit" in result


def test_non_git_dir_skips_git_log(tmp_path):
    (tmp_path / "README.md").write_text("# Test")
    result = read_project_files(str(tmp_path))
    assert "README.md" in result
