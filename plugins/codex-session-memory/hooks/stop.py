#!/usr/bin/env python3
"""Best-effort automatic save hook for Codex Stop events."""
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
SCRIPTS = PLUGIN / "scripts"
TEMP_SCOPE = Path("temps") / "2026-05-02" / "codex-session-memory-final-fixes"
INTERNAL_ENV = "CODEX_SESSION_MEMORY_INTERNAL"
LOCK_NAME = ".session-memory.lock"
LOCK_TIMEOUT_SECONDS = 0.2


def _continue() -> None:
    print(json.dumps({}))


def _load_script_module(filename: str, module_name: str):
    module_path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    return payload if isinstance(payload, dict) else {}


def _last_saved_at(frontmatter: dict) -> datetime | None:
    value = str(frontmatter.get("last_updated") or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _payload_thread_id(payload: dict) -> str:
    return str(payload.get("session_id") or "").strip()


def _payload_transcript_path(payload: dict) -> str:
    return str(payload.get("transcript_path") or "").strip()


def _tool_output_chars(delta: list[dict]) -> int:
    return sum(len(str(item.get("text", ""))) for item in delta if item.get("role") == "tool")


def _narration_env() -> dict[str, str]:
    return {**os.environ, INTERNAL_ENV: "1"}


def _save(payload: dict) -> None:
    cwd = str(payload.get("cwd") or Path.cwd())
    dotenv_loader = _load_script_module("dotenv_loader.py", "codex_session_memory_stop_dotenv_loader")
    project_root = _load_script_module("project_root.py", "codex_session_memory_stop_project_root")
    session_locator = _load_script_module("session_locator.py", "codex_session_memory_stop_session_locator")
    index_io = _load_script_module("index_io.py", "codex_session_memory_stop_index_io")
    jsonl_parser = _load_script_module("jsonl_parser.py", "codex_session_memory_stop_jsonl_parser")
    policy = _load_script_module("policy.py", "codex_session_memory_stop_policy")
    narrate = _load_script_module("narrate.py", "codex_session_memory_stop_narrate")
    context_writer = _load_script_module("context_writer.py", "codex_session_memory_stop_context_writer")
    lockfile = _load_script_module("lockfile.py", "codex_session_memory_stop_lockfile")

    thread_id = _payload_thread_id(payload)
    if not thread_id:
        return

    dotenv_loader.load_project_dotenv(cwd)
    root = Path(project_root.find_project_root(cwd))
    try:
        project_root.assert_root_is_canonical(root, cwd)
    except Exception:
        return
    transcript_path = _payload_transcript_path(payload)
    jsonl_path = Path(transcript_path) if transcript_path else session_locator.find_jsonl_by_thread(thread_id)
    if jsonl_path is None or not Path(jsonl_path).is_file():
        return

    session_dir = session_locator.data_session_dir(str(root), thread_id)
    lock_path = session_dir / LOCK_NAME
    try:
        with lockfile.acquire_lock(lock_path, timeout_seconds=LOCK_TIMEOUT_SECONDS):
            index_path = session_dir / "INDEX.md"
            frontmatter = index_io.read_frontmatter(index_path) or {}
            last_offset = int(frontmatter.get("last_processed_offset", 0))
            delta, new_offset = jsonl_parser.extract_delta(str(jsonl_path), last_offset)
            delta_chars = sum(len(str(item.get("text", ""))) for item in delta)
            decision = policy.should_save(
                delta_chars=delta_chars,
                tool_output_chars=_tool_output_chars(delta),
                last_saved_at=_last_saved_at(frontmatter),
                now=datetime.now(timezone.utc),
            )
            if not decision.save:
                return

            temp_dir = root / TEMP_SCOPE
            temp_dir.mkdir(parents=True, exist_ok=True)
            out_path = temp_dir / f"narration-{thread_id[:8]}.json"
            try:
                prompt = narrate.build_prompt(delta=delta or [{"role": "user", "text": "(no new turns; checkpoint marker only)"}])
                result = narrate.call_codex_exec(
                    prompt=prompt,
                    schema_path=SCRIPTS / "narration_schema.json",
                    out_path=out_path,
                    timeout=150,
                    env=_narration_env(),
                )
                narrate.validate(result)
                context_writer.write_context(
                    project_root=root,
                    thread_id=thread_id,
                    cwd=cwd,
                    jsonl_path=str(jsonl_path),
                    new_offset=new_offset,
                    delta=delta,
                    narration=result,
                    reason=decision.reason,
                )
            finally:
                try:
                    out_path.unlink()
                except OSError:
                    pass
    except TimeoutError:
        return


def main() -> int:
    try:
        if not os.environ.get(INTERNAL_ENV):
            _save(_read_payload())
    except Exception:
        pass
    _continue()
    return 0


if __name__ == "__main__":
    sys.exit(main())
