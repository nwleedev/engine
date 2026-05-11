#!/usr/bin/env python3
import inspect
import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent.parent / "scripts"


def _load_script_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


csm_dotenv_loader = _load_script_module(
    "dotenv_loader.py", "codex_session_memory_status_dotenv_loader"
)
csm_project_root = _load_script_module(
    "project_root.py", "codex_session_memory_status_project_root"
)
csm_session_locator = _load_script_module(
    "session_locator.py", "codex_session_memory_status_session_locator"
)
csm_jsonl_parser = _load_script_module(
    "jsonl_parser.py", "codex_session_memory_status_jsonl_parser"
)
csm_parent_locator = _load_script_module(
    "parent_locator.py", "codex_session_memory_status_parent_locator"
)
csm_graph_store = _load_script_module(
    "graph_store.py", "codex_session_memory_status_graph_store"
)
csm_index_io = _load_script_module(
    "index_io.py", "codex_session_memory_status_index_io"
)
csm_agents_rules = _load_script_module(
    "agents_rules.py", "codex_session_memory_status_agents_rules"
)

GraphStore = csm_graph_store.GraphStore


def _print_agents_rules_status(root):
    report = csm_agents_rules.check_agents_rules(root)
    print(f"AGENTS.md rules: {report.status}")
    if report.missing:
        print(f"AGENTS.md missing markers: {', '.join(report.missing)}")


def _count_child_sessions(root, thread_id):
    children_dir = csm_session_locator.child_sessions_dir(root)
    if not children_dir.is_dir():
        return 0
    count = 0
    for child in children_dir.iterdir():
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        fm = csm_index_io.read_frontmatter(child / "INDEX.md") or {}
        if fm.get("parent_session_id") == thread_id:
            count += 1
    return count


def _data_session_dir(root, thread_id, role="main"):
    parameters = inspect.signature(csm_session_locator.data_session_dir).parameters
    supports_role = "role" in parameters or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    if supports_role:
        return csm_session_locator.data_session_dir(root, thread_id, role=role)
    if role == "child":
        return csm_session_locator.child_sessions_dir(root) / thread_id
    return csm_session_locator.data_session_dir(root, thread_id)


def _artifact_session_dir(root, thread_id):
    if hasattr(csm_session_locator, "artifact_session_dir"):
        return csm_session_locator.artifact_session_dir(root, thread_id)
    return Path(root) / ".codex" / "session-memory" / "threads" / thread_id


def _resolution_child_parent_id(parent_resolution):
    parent_thread_id = getattr(parent_resolution, "parent_thread_id", None)
    if parent_thread_id:
        return str(parent_thread_id)
    return None


def _resolution_is_child(parent_resolution):
    return getattr(parent_resolution, "role", None) == "child"


def _graph_role_name(graph_role):
    if getattr(graph_role, "available", False):
        return getattr(graph_role, "role", None)
    return None


def _current_session_dir(root, thread_id, parent_resolution=None, graph_role=None):
    artifact_session_dir = _artifact_session_dir(root, thread_id)
    if (artifact_session_dir / "INDEX.md").exists():
        return artifact_session_dir

    main_session_dir = _data_session_dir(root, thread_id)
    child_session_dir = _data_session_dir(root, thread_id, role="child")
    child_index_path = child_session_dir / "INDEX.md"

    graph_role_name = _graph_role_name(graph_role)
    if graph_role_name == "main":
        return main_session_dir
    if graph_role_name == "child":
        return child_session_dir

    if child_index_path.exists():
        child_fm = csm_index_io.read_frontmatter(child_index_path) or {}
        if child_fm.get("role") == "child":
            return child_session_dir
    if _resolution_is_child(parent_resolution):
        return child_session_dir
    if (main_session_dir / "INDEX.md").exists():
        return main_session_dir
    if child_index_path.exists():
        return child_session_dir
    return main_session_dir


def _parent_index_path(root, parent_session_id):
    if not parent_session_id:
        return None
    if hasattr(csm_session_locator, "parent_session_dir"):
        return csm_session_locator.parent_session_dir(root, parent_session_id) / "INDEX.md"
    return Path(root) / ".codex" / "sessions" / parent_session_id / "INDEX.md"


def _print_child_parent_status(root, fm):
    parent_session_id = fm.get("parent_session_id") or "unknown"
    parent_index_path = _parent_index_path(root, fm.get("parent_session_id"))
    print("Role: child")
    print(f"Parent session: {parent_session_id}")
    if parent_index_path and parent_index_path.exists():
        print(f"Parent INDEX.md: {parent_index_path}")
    else:
        print("Parent INDEX.md: missing")


def _graph_parent_id(graph, thread_id):
    parent = graph.parent_of(thread_id)
    if parent.parent_thread_id:
        return str(parent.parent_thread_id)
    return None


def _print_graph_status(graph, thread_id, role):
    if not role.available:
        print("Graph: unavailable")
        return

    children = graph.children_of(thread_id)
    print(f"Role: {role.role}")
    if role.role == "child":
        print(f"Parent thread: {_graph_parent_id(graph, thread_id) or 'unknown'}")
    print(f"Direct children: {len(children)}")


def main():
    cwd = os.getcwd()
    csm_dotenv_loader.load_project_dotenv(cwd)

    thread_id = csm_session_locator.current_thread_id()
    if not thread_id:
        print("CODEX_THREAD_ID: not set (run inside a Codex session)")
        return 0

    root = csm_project_root.find_project_root(cwd)
    jsonl = csm_session_locator.find_jsonl_by_thread(thread_id)
    graph = GraphStore(codex_home=Path(root) / ".codex", include_default_home=False)
    graph_role = graph.role_of(thread_id)
    parent_resolution = csm_parent_locator.resolve_parent_thread_id(
        thread_id,
        rollout_path=jsonl,
        codex_home=Path(root) / ".codex",
    )
    session_dir = _current_session_dir(
        root,
        thread_id,
        parent_resolution=parent_resolution,
        graph_role=graph_role,
    )
    index_path = session_dir / "INDEX.md"
    contexts_dir = session_dir / "contexts"
    ctx_count = len(list(contexts_dir.glob("CONTEXT-*.md"))) if contexts_dir.is_dir() else 0

    print(f"Project root: {root}")
    print(f"Thread id: {thread_id}")
    print(f"JSONL path: {jsonl or 'missing'}")
    print(f"Artifact path: {session_dir}")
    _print_agents_rules_status(root)

    if not index_path.exists():
        print(f"Context files: {ctx_count}")
        _print_graph_status(graph, thread_id, graph_role)
        if not graph_role.available and _resolution_is_child(parent_resolution):
            _print_child_parent_status(
                root,
                {"parent_session_id": _resolution_child_parent_id(parent_resolution)},
            )
        print("Last saved: never")
        print("Pending offset: 0")
        print("status: not yet checkpointed")
        return 0

    fm = csm_index_io.read_frontmatter(index_path) or {}
    if graph_role.available:
        graph_parent_session_id = _graph_parent_id(graph, thread_id)
        is_child = graph_role.role == "child"
    else:
        graph_parent_session_id = _resolution_child_parent_id(parent_resolution)
        is_child = fm.get("role") == "child" or _resolution_is_child(parent_resolution)
    last_offset = int(fm.get("last_processed_offset", 0))
    pending = 0
    if jsonl and jsonl.is_file():
        delta, _ = csm_jsonl_parser.extract_delta(str(jsonl), last_offset)
        pending = len(delta)

    print(f"Context files: {ctx_count}")
    _print_graph_status(graph, thread_id, graph_role)
    if not graph_role.available:
        if is_child:
            child_status = dict(fm)
            if graph_parent_session_id and not child_status.get("parent_session_id"):
                child_status["parent_session_id"] = graph_parent_session_id
            _print_child_parent_status(root, child_status)
        else:
            print(f"Child sessions: {_count_child_sessions(root, thread_id)}")
    print(f"Last saved: {fm.get('last_updated') or 'never'}")
    print(f"Pending offset: {last_offset}")
    print(f"started: {fm.get('started', '?')}")
    print(f"pending_turns: {pending}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
