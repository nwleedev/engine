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


# --- load_config ---

def test_load_config_reads_version_bump_json(tmp_path):
    plugin_dir = tmp_path / "my-plugin"
    plugin_dir.mkdir()
    config = {"files": [{"path": ".claude-plugin/plugin.json", "field": "version"}]}
    (plugin_dir / ".version-bump.json").write_text(json.dumps(config))
    result = bv.load_config(plugin_dir)
    assert result["files"][0]["field"] == "version"

def test_load_config_missing_file_raises(tmp_path):
    plugin_dir = tmp_path / "no-config"
    plugin_dir.mkdir()
    try:
        bv.load_config(plugin_dir)
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

# --- get_current_version ---

def test_get_current_version_reads_first_file(tmp_path):
    plugin_dir = tmp_path / "my-plugin"
    claude_dir = plugin_dir / ".claude-plugin"
    claude_dir.mkdir(parents=True)
    (claude_dir / "plugin.json").write_text('{"version": "3.1.4"}')
    config = {"files": [{"path": ".claude-plugin/plugin.json", "field": "version"}]}
    assert bv.get_current_version(plugin_dir, config) == "3.1.4"


# --- cmd_check ---

def _make_plugin(tmp_path, name, version):
    """Helper: create a minimal plugin with .version-bump.json and plugin.json."""
    plugin_dir = tmp_path / name
    claude_dir = plugin_dir / ".claude-plugin"
    claude_dir.mkdir(parents=True)
    (claude_dir / "plugin.json").write_text(json.dumps({"version": version}, indent=2))
    config = {"files": [{"path": ".claude-plugin/plugin.json", "field": "version"}]}
    (plugin_dir / ".version-bump.json").write_text(json.dumps(config))
    return plugin_dir

def test_cmd_check_returns_true_when_in_sync(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "1.0.0")
    result = bv.cmd_check("my-plugin", plugins_dir)
    assert result is True
    out = capsys.readouterr().out
    assert "1.0.0" in out

def test_cmd_check_returns_false_when_plugin_missing(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    result = bv.cmd_check("nonexistent", plugins_dir)
    assert result is False

def test_cmd_check_prints_current_version(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "2.3.1")
    bv.cmd_check("my-plugin", plugins_dir)
    out = capsys.readouterr().out
    assert "2.3.1" in out


# --- cmd_check_all ---

def test_cmd_check_all_returns_true_when_all_in_sync(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "plugin-a", "1.0.0")
    _make_plugin(plugins_dir, "plugin-b", "2.0.0")
    result = bv.cmd_check_all(plugins_dir)
    assert result is True
    out = capsys.readouterr().out
    assert "plugin-a" in out
    assert "plugin-b" in out

def test_cmd_check_all_skips_unconfigured_plugin(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "plugin-a", "1.0.0")
    # plugin-b has no .version-bump.json -> skipped
    other = plugins_dir / "plugin-b"
    other.mkdir()
    result = bv.cmd_check_all(plugins_dir)
    assert result is True  # only plugin-a has config, it's in sync

def test_cmd_check_all_skips_dirs_without_config(tmp_path, capsys):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "unconfigured").mkdir()
    result = bv.cmd_check_all(plugins_dir)
    assert result is True
    out = capsys.readouterr().out
    assert "unconfigured" not in out


# --- cmd_bump ---

def test_cmd_bump_patch_updates_plugin_json(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "1.0.0")
    bv.cmd_bump("my-plugin", "patch", plugins_dir)
    plugin_json = plugins_dir / "my-plugin" / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert data["version"] == "1.0.1"

def test_cmd_bump_minor_updates_correctly(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "1.4.9")
    bv.cmd_bump("my-plugin", "minor", plugins_dir)
    plugin_json = plugins_dir / "my-plugin" / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert data["version"] == "1.5.0"

def test_cmd_bump_major_updates_correctly(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "2.1.3")
    bv.cmd_bump("my-plugin", "major", plugins_dir)
    plugin_json = plugins_dir / "my-plugin" / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert data["version"] == "3.0.0"

def test_cmd_bump_explicit_version(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _make_plugin(plugins_dir, "my-plugin", "1.0.0")
    bv.cmd_bump("my-plugin", "4.2.0", plugins_dir)
    plugin_json = plugins_dir / "my-plugin" / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json.read_text())
    assert data["version"] == "4.2.0"

def test_cmd_bump_missing_plugin_raises(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    try:
        bv.cmd_bump("nonexistent", "patch", plugins_dir)
        assert False, "Should have raised SystemExit"
    except SystemExit:
        pass
