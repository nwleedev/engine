"""Nearest-ancestor .env walk-up loader. Stdlib only. No-override policy."""
import os
from pathlib import Path


def _parse_line(line: str):
    line = line.split("#", 1)[0].strip()
    if "=" not in line:
        return None
    k, _, v = line.partition("=")
    k = k.strip()
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    if not k:
        return None
    return k, v


def load_project_dotenv(cwd: str):
    home = Path.home().resolve()
    start = Path(cwd).resolve()
    for d in [start, *start.parents]:
        if d == home:
            return None
        env_file = d / ".env"
        if env_file.is_file():
            for raw in env_file.read_text().splitlines():
                parsed = _parse_line(raw)
                if not parsed:
                    continue
                k, v = parsed
                if k not in os.environ:
                    os.environ[k] = v
            return env_file
    return None
