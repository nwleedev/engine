import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness_io import has_harness_dir


def extract_written_files(transcript_path: str) -> list[str]:
    written: list[str] = []
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = entry.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                for block in msg.get("content", []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in ("Write", "Edit"):
                        continue
                    file_path = block.get("input", {}).get("file_path", "")
                    if file_path and file_path not in written:
                        written.append(file_path)
    except (OSError, KeyError):
        pass
    return written


def main_with_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        return
    cwd = payload.get("cwd") or os.getcwd()
    transcript_path = payload.get("transcript_path", "")
    if not has_harness_dir(cwd) or not transcript_path:
        return
    written = extract_written_files(transcript_path)
    if not written:
        return
    file_list = "\n".join(f"  - {f}" for f in written[:20])
    context = (
        f"Files written or edited this turn:\n{file_list}\n\n"
        "Please review these files against the harness standards in "
        "`.claude/harness/`. Report any violations with severity "
        "(error/warning), file location, and improvement suggestion."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return
    main_with_payload(payload)


if __name__ == "__main__":
    main()
