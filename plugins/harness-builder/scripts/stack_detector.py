import json
from pathlib import Path
from typing import Any

DETECTION_TABLE: list[tuple[str, str]] = [
    ("package.json", "Node.js"),
    ("tsconfig.json", "TypeScript"),
    ("pyproject.toml", "Python"),
    ("requirements.txt", "Python"),
    ("pyrightconfig.json", "Python"),
    ("go.mod", "Go"),
    ("Cargo.toml", "Rust"),
    ("pom.xml", "Java"),
    ("build.gradle", "Java"),
    ("composer.json", "PHP"),
    ("Gemfile", "Ruby"),
]

FRAMEWORK_KEYS: dict[str, str] = {
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "nuxt": "Nuxt",
    "@remix-run/react": "Remix",
    "express": "Express",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
    "tailwindcss": "Tailwind CSS",
    "prisma": "Prisma",
}

LINTER_EXISTENCE: dict[str, list[str]] = {
    "eslint": [
        ".eslintrc", ".eslintrc.js", ".eslintrc.json",
        ".eslintrc.yml", ".eslintrc.yaml",
        "eslint.config.js", "eslint.config.mjs",
    ],
    "prettier": [".prettierrc", ".prettierrc.json", ".prettierrc.js", ".prettierrc.yml"],
    "golangci-lint": [".golangci.yml", ".golangci.yaml", ".golangci.toml"],
    "stylelint": [".stylelintrc", ".stylelintrc.json", ".stylelintrc.yml"],
}


def _parse_package_json(root: Path) -> dict[str, Any]:
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return {}
    try:
        return json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _detect_frameworks(pkg: dict[str, Any]) -> list[str]:
    all_deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        all_deps.update(pkg.get(section, {}))
    return [name for key, name in FRAMEWORK_KEYS.items() if key in all_deps]


def _detect_eslint_version(pkg: dict[str, Any]) -> str | None:
    all_deps: dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        all_deps.update(pkg.get(section, {}))
    spec = all_deps.get("eslint")
    if not spec:
        return None
    return spec.lstrip("^~>=< ").split(" ")[0] or None


def _detect_existing_linters(root: Path) -> list[str]:
    found = []
    for linter, patterns in LINTER_EXISTENCE.items():
        if any((root / p).exists() for p in patterns):
            found.append(linter)
    # ruff: only count if [tool.ruff] section present in pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            if "[tool.ruff]" in pyproject.read_text(encoding="utf-8"):
                found.append("ruff")
        except OSError:
            pass
    return found


def _detect_package_managers(root: Path, languages: set[str]) -> list[str]:
    managers = []
    if (root / "package.json").exists():
        if (root / "yarn.lock").exists():
            managers.append("yarn")
        elif (root / "pnpm-lock.yaml").exists():
            managers.append("pnpm")
        else:
            managers.append("npm")
    if "Python" in languages:
        managers.append("pip")
    if (root / "go.mod").exists():
        managers.append("go")
    if (root / "Cargo.toml").exists():
        managers.append("cargo")
    return managers


def _infer_missing_linters(
    languages: set[str],
    frameworks: list[str],
    existing: list[str],
) -> list[str]:
    missing = []
    js_ts = {"Node.js", "TypeScript"} & languages
    if js_ts:
        if "eslint" not in existing:
            missing.append("eslint")
        if "prettier" not in existing:
            missing.append("prettier")
        frontend = {"React", "Next.js", "Vue", "Angular", "Svelte"} & set(frameworks)
        if frontend and "stylelint" not in existing:
            missing.append("stylelint")
    if "Python" in languages and "ruff" not in existing:
        missing.append("ruff")
    if "Go" in languages and "golangci-lint" not in existing:
        missing.append("golangci-lint")
    return missing


def detect_stack(project_root: str) -> dict[str, Any]:
    root = Path(project_root)
    languages: set[str] = set()
    root_file_count = 0

    for filename, language in DETECTION_TABLE:
        if (root / filename).exists():
            languages.add(language)
            root_file_count += 1

    # Monorepo: standard files found in subdirectories but not (only) at root
    monorepo = False
    standard_names = {t[0] for t in DETECTION_TABLE}
    for subdir in root.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("."):
            sub_files = {f.name for f in subdir.iterdir() if f.is_file()}
            if sub_files & standard_names:
                monorepo = True
                for fname, lang in DETECTION_TABLE:
                    if fname in sub_files:
                        languages.add(lang)

    pkg = _parse_package_json(root)
    frameworks = _detect_frameworks(pkg)
    eslint_version = _detect_eslint_version(pkg)
    linters_existing = _detect_existing_linters(root)
    linters_missing = _infer_missing_linters(languages, frameworks, linters_existing)
    package_managers = _detect_package_managers(root, languages)

    result: dict[str, Any] = {
        "languages": sorted(languages),
        "frameworks": frameworks,
        "linters_existing": linters_existing,
        "linters_missing": linters_missing,
        "monorepo": monorepo,
        "package_managers": package_managers,
        "confidence": "high" if root_file_count >= 2 else "low",
    }
    if eslint_version:
        result["eslint_version"] = eslint_version
    return result
