import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import bump_version as bv


# --- bump_semver ---

def test_bump_semver_patch():
    assert bv.bump_semver("1.2.3", "patch") == "1.2.4"

def test_bump_semver_minor_resets_patch():
    assert bv.bump_semver("1.2.3", "minor") == "1.3.0"

def test_bump_semver_major_resets_minor_and_patch():
    assert bv.bump_semver("1.2.3", "major") == "2.0.0"

def test_bump_semver_explicit_version():
    assert bv.bump_semver("1.0.0", "2.5.1") == "2.5.1"

def test_bump_semver_invalid_type_raises():
    try:
        bv.bump_semver("1.0.0", "hotfix")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# --- read_json_field ---

def test_read_json_field_top_level(tmp_path):
    f = tmp_path / "plugin.json"
    f.write_text('{"version": "1.2.3"}')
    assert bv.read_json_field(f, "version") == "1.2.3"

def test_read_json_field_nested(tmp_path):
    f = tmp_path / "marketplace.json"
    f.write_text('{"plugins": [{"name": "foo", "version": "2.0.0"}]}')
    assert bv.read_json_field(f, "plugins.0.version") == "2.0.0"

# --- write_json_field ---

def test_write_json_field_top_level(tmp_path):
    f = tmp_path / "plugin.json"
    f.write_text('{"version": "1.0.0", "name": "test"}')
    bv.write_json_field(f, "version", "1.1.0")
    data = json.loads(f.read_text())
    assert data["version"] == "1.1.0"
    assert data["name"] == "test"

def test_write_json_field_nested(tmp_path):
    f = tmp_path / "marketplace.json"
    f.write_text('{"plugins": [{"name": "foo", "version": "1.0.0"}]}')
    bv.write_json_field(f, "plugins.0.version", "1.5.0")
    data = json.loads(f.read_text())
    assert data["plugins"][0]["version"] == "1.5.0"

def test_write_json_field_preserves_other_fields(tmp_path):
    f = tmp_path / "plugin.json"
    f.write_text('{"name": "keep-me", "version": "1.0.0", "author": {"name": "dev"}}')
    bv.write_json_field(f, "version", "2.0.0")
    data = json.loads(f.read_text())
    assert data["name"] == "keep-me"
    assert data["author"]["name"] == "dev"
