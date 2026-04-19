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
