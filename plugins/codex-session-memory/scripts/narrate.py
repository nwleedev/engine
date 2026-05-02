"""Wrap codex-exec --ephemeral --output-schema for narration generation."""
import json
import subprocess
from pathlib import Path


REQUIRED_FIELDS = ("title", "what_why", "decisions", "open", "next")
DEFAULT_TIMEOUT = 180


class NarrationError(RuntimeError):
    pass


_PROMPT_KO = (
    "다음은 Codex 세션 트랜스크립트의 일부다. 제공된 JSON Schema에 정확히 부합하는 "
    "JSON 객체로 요약하라. 한국어로 작성하고, JSON 외 다른 출력 금지.\n\n{delta}"
)

_PROMPT_EN = (
    "Below is a fragment of a Codex session transcript. Summarize as a JSON object "
    "matching the provided schema. English only. Output JSON object only.\n\n{delta}"
)


def build_prompt(delta: list, lang: str = "en") -> str:
    delta_text = "\n".join(f"[{m['role']}] {m['text']}" for m in delta)
    template = _PROMPT_KO if lang == "ko" else _PROMPT_EN
    return template.format(delta=delta_text)


def call_codex_exec(prompt: str, schema_path: Path, out_path: Path, timeout: int = DEFAULT_TIMEOUT) -> dict:
    cmd = [
        "codex", "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--output-schema", str(schema_path),
        "--output-last-message", str(out_path),
        "--color", "never",
        prompt,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise NarrationError(f"codex exec timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise NarrationError("codex binary not found in PATH") from e

    if r.returncode != 0:
        raise NarrationError(f"codex exec failed (rc={r.returncode}): {(r.stderr or r.stdout)[:300]}")

    try:
        text = Path(out_path).read_text()
    except OSError as e:
        raise NarrationError(f"output file unreadable: {e}") from e

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise NarrationError(f"invalid JSON output: {text[:200]}") from e


def validate(result: dict) -> None:
    for field in REQUIRED_FIELDS:
        if field not in result:
            raise NarrationError(f"missing required field: {field}")
