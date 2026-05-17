"""Manage flat Codex session-memory artifacts by thread id."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA_VERSION = 2
RELATIONSHIP_SOURCE_FIELDS = {"role", "parent_session_id"}
CONTEXT_HEADING = "## Contexts"
RESUME_HINT = "Resume this session: `$session-memory:resume {session_prefix}`"


class ArtifactStore:
    """Path and INDEX.md helper for CODEX_SESSION_ID flat artifacts."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)

    def root(self) -> Path:
        return self.project_root / ".codex" / "session-memory"

    def threads_root(self) -> Path:
        return self.root() / "threads"

    def thread_dir(self, thread_id: str) -> Path:
        return self.threads_root() / thread_id

    def index_path(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "INDEX.md"

    def contexts_dir(self, thread_id: str) -> Path:
        return self.thread_dir(thread_id) / "contexts"

    def context_filename(self, *, timestamp: str, task_id: str, nonce: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", task_id.lower()).strip("-")
        if not slug:
            slug = "checkpoint"
        return f"CONTEXT-{timestamp}-{slug}-{nonce}.md"

    def context_path(self, thread_id: str, filename: str) -> Path:
        return self.contexts_dir(thread_id) / filename

    def legacy_index_candidates(self, thread_id: str) -> list[Path]:
        sessions = self.project_root / ".codex" / "sessions"
        candidates = [
            sessions / thread_id / "INDEX.md",
            sessions / "_children" / thread_id / "INDEX.md",
        ]
        return [path for path in candidates if path.is_file()]

    def write_index(
        self,
        thread_id: str,
        *,
        frontmatter: dict[str, Any],
        contexts: list[dict[str, str]],
    ) -> None:
        index_path = self.index_path(thread_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        clean_frontmatter = {
            key: value
            for key, value in frontmatter.items()
            if key not in RELATIONSHIP_SOURCE_FIELDS
        }
        clean_frontmatter.setdefault("thread_id", thread_id)
        clean_frontmatter.setdefault("artifact_schema_version", ARTIFACT_SCHEMA_VERSION)

        lines = ["---"]
        for key, value in clean_frontmatter.items():
            lines.append(f"{key}: {value}")
        lines.extend(["---", "", "# Session Summary", "", "(in progress)", "", CONTEXT_HEADING, ""])
        for context in contexts:
            lines.append(f"- [{context['filename']}] — {context['summary']}")
        lines.extend(["", "---"])
        session_prefix = str(clean_frontmatter.get("session_id", ""))[:8]
        lines.append(RESUME_HINT.format(session_prefix=session_prefix))
        lines.append("")

        index_path.write_text("\n".join(lines), encoding="utf-8")
