import subprocess


def test_validate_harness_foundry_script_passes():
    result = subprocess.run(
        ["python3", "plugins/harness-foundry/scripts/validate_harness_foundry.py"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert "harness-foundry validation passed" in result.stdout
