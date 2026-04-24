import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from feedback_io import append_raw_entry

_MIN_ANSWER_LEN = 200

_ANALYSIS_PROMPT_TEMPLATE = """\
You are evaluating Claude Code assistant responses for vague or unhelpful quality.

NOT vague — do NOT flag these patterns:
- Yes/no answers or short status confirmations ("Done", "Fixed", "Yes, that's correct")
- Clarifying questions asking the user for more information
- Code-only responses (a code block with minimal prose)
- Single-sentence factual answers to direct factual questions
- Responses under 100 characters

Q+R pairs to evaluate (index, question, answer):
{pairs_section}

Select at most 3 highest-confidence vague responses from the list above.
A response is vague when it: uses generic phrases without specifics, omits reasoning steps, states conclusions without evidence, or uses "several/various/some" without elaboration.

Reply with a JSON array only:
[{{"index": <int>, "reason": "<one sentence>", "confidence": "high"|"medium"|"low"}}, ...]

If no responses are vague, reply with an empty array: []
"""


def _extract_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def extract_qr_pairs(transcript: str) -> list[dict]:
    pairs = []
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    i = 0
    while i < len(lines):
        try:
            entry = json.loads(lines[i])
        except json.JSONDecodeError:
            i += 1
            continue
        msg = entry.get("message", {})
        if msg.get("role") == "user":
            question = _extract_text(msg.get("content", ""))
            if i + 1 < len(lines):
                try:
                    next_entry = json.loads(lines[i + 1])
                except json.JSONDecodeError:
                    i += 1
                    continue
                next_msg = next_entry.get("message", {})
                if next_msg.get("role") == "assistant":
                    answer = _extract_text(next_msg.get("content", ""))
                    if len(answer) >= _MIN_ANSWER_LEN:
                        pairs.append({
                            "index": len(pairs),
                            "question": question,
                            "answer": answer,
                        })
                    i += 2
                    continue
        i += 1
    return pairs


def build_analysis_prompt(pairs: list[dict]) -> str:
    pairs_section_lines = []
    for p in pairs:
        pairs_section_lines.append(
            f"[{p['index']}] Q: {p['question']}\n    A: {p['answer'][:500]}"
        )
    pairs_section = "\n\n".join(pairs_section_lines)
    return _ANALYSIS_PROMPT_TEMPLATE.format(pairs_section=pairs_section)


def parse_analysis_result(result_text: str) -> list[dict]:
    pos = 0
    while True:
        start = result_text.find("[", pos)
        if start < 0:
            return []
        try:
            obj, _ = json.JSONDecoder().raw_decode(result_text[start:])
            if isinstance(obj, list):
                return [
                    item for item in obj
                    if isinstance(item, dict) and item.get("confidence") == "high"
                ]
            pos = start + 1
        except json.JSONDecodeError:
            pos = start + 1


def record_detections(cwd: str, pairs: list[dict], detections: list[dict]) -> None:
    if not detections:
        return
    for det in detections:
        idx = det.get("index", 0)
        reason = det.get("reason", "vague response detected")
        pair = next((p for p in pairs if p["index"] == idx), None)
        question_snippet = pair["question"][:80] if pair else "unknown"
        entry_text = f"[auto-detected] {reason} (Q: {question_snippet!r})"
        append_raw_entry(cwd, entry_text)

    pending_path = Path(cwd) / ".claude" / "quality" / "pending_review.txt"
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    existing = 0
    if pending_path.exists():
        try:
            existing = int(pending_path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing = 0
    pending_path.write_text(str(existing + len(detections)), encoding="utf-8")


def run_quality_analysis(payload: dict, cwd: str) -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        return
    transcript_path = payload.get("transcript_path", "")
    if not transcript_path:
        return
    path = Path(transcript_path)
    if not path.exists():
        return
    transcript = path.read_text(encoding="utf-8")
    pairs = extract_qr_pairs(transcript)
    if not pairs:
        return
    prompt = build_analysis_prompt(pairs)
    env = {**os.environ, "CLAUDE_WRITING_CONTEXT": "1"}
    try:
        r = subprocess.run(
            [
                "claude", "-p",
                "--model", "claude-haiku-4-5-20251001",
                "--no-session-persistence",
                "--output-format", "json",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        if r.returncode != 0:
            return
        outer = json.loads(r.stdout)
        result_text = outer.get("result", "")
        detections = parse_analysis_result(result_text)
        record_detections(cwd, pairs, detections)
    except Exception:
        return
