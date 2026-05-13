from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "plugin-sources/session-memory/adapters/codex"
GENERATED_ROOT = ROOT / "plugins/codex/session-memory"


def _python_files() -> list[Path]:
    return sorted(SOURCE_ROOT.rglob("*.py"))


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _has_future_annotations(module: ast.Module) -> bool:
    return any(
        isinstance(statement, ast.ImportFrom)
        and statement.module == "__future__"
        and any(alias.name == "annotations" for alias in statement.names)
        for statement in module.body[:10]
    )


def _annotation_nodes(module: ast.Module) -> list[ast.AST]:
    annotations: list[ast.AST] = []
    for node in ast.walk(module):
        if isinstance(node, (ast.AnnAssign, ast.arg)) and node.annotation is not None:
            annotations.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns is not None:
                annotations.append(node.returns)
    return annotations


def _is_annotated_name(node: ast.AST) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Annotated") or (
        isinstance(node, ast.Attribute) and node.attr == "Annotated"
    )


def _is_literal_name(node: ast.AST) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Literal") or (
        isinstance(node, ast.Attribute) and node.attr == "Literal"
    )


def _subscript_type_args(node: ast.Subscript) -> list[ast.AST]:
    if isinstance(node.slice, ast.Tuple):
        elements = list(node.slice.elts)
    else:
        elements = [node.slice]
    if _is_literal_name(node.value):
        return []
    if _is_annotated_name(node.value):
        return elements[:1]
    return elements


def _contains_pep604_type_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return True
    if isinstance(node, ast.Subscript):
        return any(_contains_pep604_type_expr(arg) for arg in _subscript_type_args(node))
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_contains_pep604_type_expr(element) for element in node.elts)
    return False


def _has_bit_or_annotation(module: ast.Module) -> bool:
    return any(_contains_pep604_type_expr(annotation) for annotation in _annotation_nodes(module))


def test_pep604_detection_checks_type_positions_only() -> None:
    flagged_annotations = [
        "value: str | None",
        "value: list[str | None]",
        "value: dict[str, tuple[int | None, ...]]",
        "value: Callable[[str | None], int]",
        "value: Annotated[list[int | None], re.I | re.M]",
    ]
    ignored_annotations = ["value: Annotated[int, re.I | re.M]", "value: Literal[re.I | re.M]"]

    for source in flagged_annotations:
        assert _has_bit_or_annotation(ast.parse(source, feature_version=(3, 9)))
    for source in ignored_annotations:
        assert not _has_bit_or_annotation(ast.parse(source, feature_version=(3, 9)))


def _tomllib_import_lines(module: ast.Module) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Import) and any(alias.name == "tomllib" for alias in node.names):
            lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module == "tomllib":
            lines.append(node.lineno)
    return lines


def test_codex_session_memory_sources_parse_as_python39() -> None:
    files = _python_files()
    assert files

    failures: list[str] = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        except SyntaxError as exc:
            failures.append(f"{_relative(path)}:{exc.lineno}: {exc.msg}")

    assert failures == []


def test_codex_session_memory_sources_do_not_use_runtime_pep604_annotations() -> None:
    failures: list[str] = []
    for path in _python_files():
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        if _has_bit_or_annotation(module) and not _has_future_annotations(module):
            failures.append(_relative(path))

    assert failures == []


def test_codex_session_memory_sources_do_not_import_tomllib_directly() -> None:
    failures: list[str] = []
    for path in _python_files():
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        failures.extend(f"{_relative(path)}:{line}" for line in _tomllib_import_lines(module))

    assert failures == []


def test_codex_session_memory_generated_tomli_compatibility_files_exist() -> None:
    assert (GENERATED_ROOT / "_packages/tomli/__init__.py").is_file()
    assert (GENERATED_ROOT / "scripts/toml_compat.py").is_file()
