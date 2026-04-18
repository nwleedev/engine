import sys
from pathlib import Path
from unittest import mock
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/harness-engineer/scripts"
PLUGIN_ROOT = Path(__file__).parent.parent.parent / "plugins/harness-engineer"
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_harness as gh


# --- detect_project_domains ---

def test_detect_project_domains_tsx(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}", encoding="utf-8")
    result = gh.detect_project_domains(str(tmp_path))
    assert "react-frontend" in result


def test_detect_project_domains_python(tmp_path):
    (tmp_path / "app.py").write_text("print('hello')", encoding="utf-8")
    result = gh.detect_project_domains(str(tmp_path))
    assert "python-backend" in result


def test_detect_project_domains_empty(tmp_path):
    result = gh.detect_project_domains(str(tmp_path))
    assert result == []


def test_detect_project_domains_no_duplicates(tmp_path):
    (tmp_path / "a.tsx").write_text("", encoding="utf-8")
    (tmp_path / "b.tsx").write_text("", encoding="utf-8")
    result = gh.detect_project_domains(str(tmp_path))
    assert result.count("react-frontend") == 1


# --- get_template ---

def test_get_template_react_exists():
    content = gh.get_template("react-frontend", str(PLUGIN_ROOT))
    assert "react-frontend" in content.lower() or "React" in content


def test_get_template_unknown_domain():
    content = gh.get_template("unknown-domain", str(PLUGIN_ROOT))
    assert "unknown-domain" in content  # generic template fallback


# --- build_harness_frontmatter ---

def test_build_harness_frontmatter_ko():
    result = gh.build_harness_frontmatter("react-frontend", "ko")
    assert "language: ko" in result
    assert "domain: react-frontend" in result


def test_build_harness_frontmatter_includes_today():
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    result = gh.build_harness_frontmatter("react-frontend", "en")
    assert today in result


# --- generate_harness_file ---

def test_generate_harness_file_replaces_frontmatter_language():
    content = gh.generate_harness_file("react-frontend", "/tmp/proj", "ko", str(PLUGIN_ROOT))
    assert "language: ko" in content


def test_generate_harness_file_replaces_frontmatter_date():
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    content = gh.generate_harness_file("react-frontend", "/tmp/proj", "en", str(PLUGIN_ROOT))
    assert f"updated: {today}" in content
