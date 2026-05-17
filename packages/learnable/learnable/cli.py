from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

from learnable.core.config import default_server_config
from learnable.core.paths import resolve_project_root
from learnable.core.redaction import redact_text
from learnable.materials.events import read_audits, read_events
from learnable.materials.file_store import FileMaterialStore
from learnable.materials.graph import validate_graph_integrity
from learnable.materials.schemas import (
    validate_graph_record,
    validate_material_record,
    validate_session_record,
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    project_root = _project_root(args.project_root)
    try:
        if args.command == "init":
            return _init(project_root)
        if args.command == "ask":
            return _ask(project_root, args)
        if args.command == "explain":
            return _explain(project_root, args)
        if args.command == "status":
            return _status(project_root)
        if args.command == "validate":
            return _validate(project_root)
    except Exception as exc:
        _print_error(str(exc))
        return 1
    _print_error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="learnable")
    parser.add_argument("--project-root", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init")

    ask = subparsers.add_parser("ask")
    ask.add_argument("--title", required=True)
    ask.add_argument("--prompt", required=True)
    ask.add_argument("--markdown-file")

    explain = subparsers.add_parser("explain")
    explain.add_argument("--session", required=True)
    explain.add_argument("--parent", required=True)
    explain.add_argument("--title", required=True)
    explain.add_argument("--prompt", required=True)
    explain.add_argument("--markdown-file")

    subparsers.add_parser("status")
    subparsers.add_parser("validate")
    return parser


def _project_root(value: str | None) -> Path:
    if value is not None:
        return Path(value).resolve()
    return resolve_project_root(Path.cwd())


def _init(project_root: Path) -> int:
    FileMaterialStore(project_root).init()
    print("initialized materials_root=.codex/materials")
    return 0


def _ask(project_root: Path, args: argparse.Namespace) -> int:
    markdown = _read_markdown(project_root, args.markdown_file)
    session = FileMaterialStore(project_root).create_session(
        title=args.title,
        prompt=args.prompt,
        markdown=markdown,
        provenance=_provenance(),
    )
    print(f"learnable_session_id={session['learnable_session_id']}")
    print(f"root_node_id={session['root_node_id']}")
    return 0


def _explain(project_root: Path, args: argparse.Namespace) -> int:
    markdown = _read_markdown(project_root, args.markdown_file)
    material = FileMaterialStore(project_root).add_child(
        learnable_session_id=args.session,
        parent_node_id=args.parent,
        title=args.title,
        prompt=args.prompt,
        markdown=markdown,
        provenance=_provenance(),
    )
    print(f"node_id={material['node_id']}")
    return 0


def _status(project_root: Path) -> int:
    root = _materials_root_path(project_root)
    if root.exists():
        index = _read_json(root / "index.json")
        sessions = index.get("sessions")
        if not isinstance(sessions, list):
            raise ValueError("material index sessions must be a list")
        sessions_count = len(sessions)
        schema_version = index.get("schema_version", "unknown")
    else:
        sessions_count = 0
        schema_version = "missing"
    print("materials_root=.codex/materials")
    print(f"server_config={_presence(root / '.server' / 'config.json')}")
    print(f"sessions_count={sessions_count}")
    print(f"schema_version={schema_version}")
    return 0


def _presence(path: Path) -> str:
    return "present" if path.exists() else "missing"


def _validate(project_root: Path) -> int:
    root = _materials_root_path(project_root)
    index = _read_json(root / "index.json")
    if index.get("schema_version") != "1.0":
        raise ValueError("invalid index schema version")
    sessions = index.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("material index sessions must be a list")

    _validate_server_metadata(root)
    read_audits(root / ".server" / "audits.jsonl")
    indexed_session_ids = set()
    for item in sessions:
        if not isinstance(item, Mapping):
            raise ValueError("material index session entry must be an object")
        session_id = item.get("learnable_session_id")
        if not isinstance(session_id, str):
            raise ValueError("material index session id must be a string")
        indexed_session_ids.add(session_id)
        _validate_session(root, session_id)

    sessions_root = root / "sessions"
    if sessions_root.exists():
        actual_session_ids = {
            path.name for path in sessions_root.iterdir() if path.is_dir()
        }
        extra_session_ids = actual_session_ids - indexed_session_ids
        if extra_session_ids:
            raise ValueError("orphan session directory")

    print("valid")
    return 0


def _validate_session(root: Path, session_id: str) -> None:
    session_dir = root / "sessions" / session_id
    session = _read_json(session_dir / "session.json")
    graph = _read_json(session_dir / "graph.json")
    validate_session_record(session)
    validate_graph_record(graph)
    if session.get("learnable_session_id") != session_id:
        raise ValueError("session id mismatch")
    if graph.get("learnable_session_id") != session_id:
        raise ValueError("graph session id mismatch")
    if session.get("root_node_id") != graph.get("root_node_id"):
        raise ValueError("session root node mismatch")
    materials = _materials_by_node(session_dir)
    validate_graph_integrity(
        graph,
        material_node_ids=set(materials),
        material_records_by_node=materials,
    )
    _validate_node_directories(session_dir, set(materials))
    for node_id in materials:
        markdown_path = session_dir / "nodes" / node_id / "node.md"
        markdown = markdown_path.read_text(encoding="utf-8")
        if not markdown.strip():
            raise ValueError("missing markdown body")
    read_events(session_dir / "events.jsonl")


def _validate_server_metadata(root: Path) -> None:
    project_root = root.parent.parent
    config = _read_json(root / ".server" / "config.json")
    expected = default_server_config(project_root)
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"invalid server config {key}")
    token_path = root / ".server" / "token"
    if not token_path.read_text(encoding="utf-8").strip():
        raise ValueError("missing server token")


def _materials_by_node(session_dir: Path) -> dict[str, Mapping[str, object]]:
    nodes_root = session_dir / "nodes"
    materials: dict[str, Mapping[str, object]] = {}
    if not nodes_root.exists():
        return materials
    for material_path in nodes_root.glob("*/material.json"):
        material = _read_json(material_path)
        validate_material_record(material)
        node_id = material.get("node_id")
        if not isinstance(node_id, str):
            raise ValueError("material node id must be a string")
        materials[node_id] = material
    return materials


def _validate_node_directories(session_dir: Path, material_node_ids: set[str]) -> None:
    nodes_root = session_dir / "nodes"
    if not nodes_root.exists():
        raise ValueError("missing nodes directory")
    actual_node_ids = {path.name for path in nodes_root.iterdir() if path.is_dir()}
    if actual_node_ids != material_node_ids:
        raise ValueError("orphan node directory")


def _read_markdown(project_root: Path, markdown_file: str | None) -> str:
    if markdown_file is not None:
        path = Path(markdown_file)
        if not path.is_absolute():
            path = project_root / path
        try:
            markdown = path.read_text(encoding="utf-8")
        except OSError as exc:
            display_path = _display_path(project_root, path)
            raise ValueError(
                f"unreadable markdown file: {display_path} ({type(exc).__name__})"
            ) from exc
    else:
        if sys.stdin.isatty():
            raise ValueError("missing markdown source")
        markdown = sys.stdin.read()
    if not markdown.strip():
        raise ValueError("empty markdown")
    return markdown


def _materials_root_path(project_root: Path) -> Path:
    return project_root / ".codex" / "materials"


def _display_path(project_root: Path, path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(project_root))
    except ValueError:
        return path.name


def _read_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object JSON at {path}")
    return data


def _provenance() -> dict[str, object]:
    return {"runtime": "codex"}


def _print_error(message: str) -> None:
    print(f"error: {redact_text(message)}", file=sys.stderr)
