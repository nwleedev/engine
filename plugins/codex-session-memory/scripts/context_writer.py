"""Shared context writer used by skills and hooks."""
import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_sibling(script_name: str):
    module_name = f"_codex_session_memory_{script_name}"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(module_name, HERE / f"{script_name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


evidence_extractor = _load_sibling("evidence_extractor")
index_io = _load_sibling("index_io")
session_locator = _load_sibling("session_locator")


@dataclass(frozen=True)
class WriteResult:
    context_path: Path
    index_path: Path


def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.strip())
    return safe[:60].strip("-") or "checkpoint"


def _render_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- 없음"]


def _render_context(narration: dict, evidence: dict, reason: str) -> str:
    lines = [
        f"# {narration['title']}",
        "",
        "## 무엇을/왜",
        narration["what_why"],
        "",
        "## 결정",
        *_render_list(narration.get("decisions") or []),
        "",
        "## 미완료",
        *_render_list(narration.get("open") or []),
        "",
        "## 다음",
        narration["next"],
        "",
        "## Evidence",
        f"- save_reason: {reason}",
        "",
        "### Files",
        *_render_list(evidence["files"]),
        "",
        "### Commands",
        *_render_list(evidence["commands"]),
        "",
        "### Failures",
        *_render_list(evidence["failures"]),
        "",
        "### Sources",
        *_render_list(evidence["sources"]),
        "",
    ]
    return "\n".join(lines)


def _unique_context_path(contexts_dir: Path, base_filename: str) -> Path:
    candidate = contexts_dir / base_filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 2
    while True:
        candidate = contexts_dir / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def write_context(
    *,
    project_root: Path,
    thread_id: str,
    cwd: str,
    jsonl_path: str,
    new_offset: int,
    delta: list[dict],
    narration: dict,
    reason: str,
) -> WriteResult:
    session_dir = session_locator.data_session_dir(str(project_root), thread_id)
    contexts_dir = session_dir / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    index_path = session_dir / "INDEX.md"

    now = datetime.now().strftime("%Y%m%d-%H%M")
    ctx_filename = f"CONTEXT-{now}-{_slug(narration['title'])}.md"
    ctx_path = _unique_context_path(contexts_dir, ctx_filename)
    ctx_filename = ctx_path.name
    evidence = evidence_extractor.extract_evidence(delta)
    ctx_path.write_text(_render_context(narration, evidence, reason))

    if not index_path.exists():
        index_io.write_index(
            index_path,
            frontmatter={
                "session_id": thread_id,
                "cwd": cwd,
                "started": _now_iso(),
                "last_updated": _now_iso(),
                "last_processed_offset": new_offset,
                "jsonl_path": jsonl_path,
            },
            contexts=[],
        )

    summary = (narration["what_why"] or "").splitlines()[0][:180]
    index_io.append_context_entry(index_path, filename=ctx_filename, summary=summary)
    index_io.update_frontmatter(index_path, last_processed_offset=new_offset, last_updated=_now_iso())
    return WriteResult(context_path=ctx_path, index_path=index_path)
