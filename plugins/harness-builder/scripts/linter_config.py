from pathlib import Path

_LINTER_TABLE: dict[str, tuple[str, str]] = {
    "prettier": (".prettierrc.json", "json"),
    "ruff": ("pyproject.toml", "toml-section"),
    "golangci-lint": (".golangci.yml", "yaml"),
    "stylelint": (".stylelintrc.json", "json"),
    "clippy": ("Cargo.toml", "toml-section"),
}

_ESLINT_EXISTENCE = [
    ".eslintrc", ".eslintrc.js", ".eslintrc.json",
    ".eslintrc.yml", ".eslintrc.yaml",
    "eslint.config.js", "eslint.config.mjs",
]

_EXISTENCE_MAP: dict[str, list[str]] = {
    "eslint": _ESLINT_EXISTENCE,
    "prettier": [".prettierrc", ".prettierrc.json", ".prettierrc.js", ".prettierrc.yml"],
    "golangci-lint": [".golangci.yml", ".golangci.yaml", ".golangci.toml"],
    "stylelint": [".stylelintrc", ".stylelintrc.json", ".stylelintrc.yml"],
}


def _parse_major(version: str) -> int:
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError):
        return 9


def get_linter_config_path(linter: str, version: str | None, project_root: str) -> tuple[str, str]:
    root = Path(project_root)
    if linter == "eslint":
        major = _parse_major(version) if version else 9
        if major >= 9:
            return str(root / "eslint.config.js"), "flat"
        return str(root / ".eslintrc.json"), "legacy"
    if linter in _LINTER_TABLE:
        filename, fmt = _LINTER_TABLE[linter]
        return str(root / filename), fmt
    raise ValueError(f"Unknown linter: {linter}")


def should_skip_existing(linter: str, project_root: str) -> bool:
    root = Path(project_root)
    patterns = _EXISTENCE_MAP.get(linter, [])
    for pattern in patterns:
        if (root / pattern).exists():
            return True
    if linter == "ruff":
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                return "[tool.ruff]" in pyproject.read_text(encoding="utf-8")
            except OSError:
                pass
        return False
    if linter in ("clippy",):
        cargo = root / "Cargo.toml"
        if cargo.exists():
            try:
                return "[lints]" in cargo.read_text(encoding="utf-8")
            except OSError:
                pass
        return False
    return False
