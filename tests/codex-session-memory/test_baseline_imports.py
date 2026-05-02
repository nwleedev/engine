import importlib.util
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "codex-session-memory"
SCRIPTS = PLUGIN / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_main_poc_scripts_are_importable():
    for name in [
        "dotenv_loader",
        "index_io",
        "jsonl_parser",
        "narrate",
        "project_root",
        "session_locator",
    ]:
        assert load_script(name) is not None
