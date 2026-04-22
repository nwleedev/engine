import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "plugins/nondev-builder/scripts"))
from nondev_io import (
    ensure_dirs,
    read_index,
    read_rubric,
    read_skill,
    upsert_domain,
    write_rubric,
    write_skill,
)


def test_read_index_returns_none_when_missing(tmp_path):
    assert read_index(str(tmp_path)) is None


def test_upsert_domain_creates_index(tmp_path):
    entry = {
        "task_name": "market-research",
        "display_name": "시장 조사",
        "command": "/market-research",
        "keywords": {"ko": ["시장"], "en": ["market"]},
    }
    upsert_domain(str(tmp_path), entry)
    index = read_index(str(tmp_path))
    assert index is not None
    assert len(index["domains"]) == 1
    assert index["domains"][0]["task_name"] == "market-research"


def test_upsert_domain_updates_existing(tmp_path):
    entry_v1 = {
        "task_name": "market-research",
        "display_name": "시장 조사",
        "command": "/market-research",
        "keywords": {"ko": ["시장"], "en": ["market"]},
    }
    upsert_domain(str(tmp_path), entry_v1)
    entry_v2 = {
        "task_name": "market-research",
        "display_name": "Market Research",
        "command": "/market-research",
        "keywords": {"ko": ["시장", "경쟁사"], "en": ["market", "competitor"]},
    }
    upsert_domain(str(tmp_path), entry_v2)
    index = read_index(str(tmp_path))
    assert len(index["domains"]) == 1
    assert index["domains"][0]["display_name"] == "Market Research"
    assert "경쟁사" in index["domains"][0]["keywords"]["ko"]


def test_upsert_domain_appends_new_domain(tmp_path):
    for name in ["market-research", "stock-analysis"]:
        upsert_domain(str(tmp_path), {
            "task_name": name,
            "display_name": name,
            "command": f"/{name}",
            "keywords": {"ko": [], "en": []},
        })
    index = read_index(str(tmp_path))
    assert len(index["domains"]) == 2


def test_read_skill_returns_none_when_missing(tmp_path):
    assert read_skill(str(tmp_path), "market-research") is None


def test_write_read_skill_roundtrip(tmp_path):
    content = "# Market Research Methodology\n\n## Core Framework\nUse TAM/SAM/SOM."
    write_skill(str(tmp_path), "market-research", content)
    assert read_skill(str(tmp_path), "market-research") == content


def test_write_skill_creates_dirs(tmp_path):
    write_skill(str(tmp_path), "new-domain", "# Content")
    path = tmp_path / ".claude" / "nondev" / "new-domain" / "skill.md"
    assert path.exists()


def test_read_rubric_returns_none_when_missing(tmp_path):
    assert read_rubric(str(tmp_path), "market-research") is None


def test_write_read_rubric_roundtrip(tmp_path):
    content = "# Rubric\n## Violation Criteria\n| id | Violation |"
    write_rubric(str(tmp_path), "market-research", content)
    assert read_rubric(str(tmp_path), "market-research") == content


def test_ensure_dirs_creates_all_paths(tmp_path):
    ensure_dirs(str(tmp_path), "prd-writing")
    assert (tmp_path / ".claude" / "nondev" / "prd-writing").is_dir()
    assert (tmp_path / ".claude" / "commands").is_dir()


def test_index_has_version_and_updated(tmp_path):
    upsert_domain(str(tmp_path), {
        "task_name": "t",
        "display_name": "T",
        "command": "/t",
        "keywords": {"ko": [], "en": []},
    })
    index = read_index(str(tmp_path))
    assert "version" in index
    assert "updated" in index
