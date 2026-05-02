"""Project-local temporary path helpers."""
from datetime import datetime
from pathlib import Path


def project_temp_dir(project_root: Path, scope: str, now: datetime | None = None) -> Path:
    current = now or datetime.now().astimezone()
    return Path(project_root) / "temps" / current.date().isoformat() / scope
