import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
TEMP_PATHS = PLUGIN / "scripts" / "temp_paths.py"


def load_temp_paths():
    module_name = "test_codex_session_memory_temp_paths"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, TEMP_PATHS)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_project_temp_dir_uses_project_root_date_and_scope(tmp_path):
    temp_paths = load_temp_paths()

    result = temp_paths.project_temp_dir(
        tmp_path,
        "codex-session-memory-checkpoint",
        now=datetime(2099, 1, 2, 3, 4, tzinfo=timezone.utc),
    )

    assert result == tmp_path / "temps" / "2099-01-02" / "codex-session-memory-checkpoint"
