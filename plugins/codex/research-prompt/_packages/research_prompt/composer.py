"""Compose single-file Markdown prompts for Deep Research."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptInput:
    """Structured data used to compose the Deep Research markdown prompt."""

    problem: str
    context: list[str] = field(default_factory=list)
    code_blocks: list[dict[str, str]] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    reproduction: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    research_goals: list[str] = field(default_factory=list)
    expected_output: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _list_or_default(items: list[str]) -> str:
    """Render a Markdown list or an explicit absence marker."""

    if not items:
        return "Not provided."
    return "\n".join(f"- {item}" for item in items)


def _numbered_or_default(items: list[str]) -> str:
    """Render ordered reproduction steps or an explicit absence marker."""

    if not items:
        return "Not provided."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _code_or_default(blocks: list[dict[str, str]]) -> str:
    """Render relevant code excerpts with path and relevance reason."""

    if not blocks:
        return "Not provided."
    rendered: list[str] = []
    for block in blocks:
        rendered.append(f"## `{block['path']}`")
        rendered.append(f"Reason: {block['reason']}")
        rendered.append("")
        rendered.append("```text")
        rendered.append(block["excerpt"].rstrip())
        rendered.append("```")
    return "\n".join(rendered)


def compose_prompt(data: PromptInput) -> str:
    """Compose the final single Markdown prompt artifact."""

    warnings = ""
    if data.warnings:
        warnings = "\n\n## Collection Warnings\n\n" + _list_or_default(data.warnings)

    return "\n\n".join(
        [
            "# Problem\n\n" + (data.problem or "Not provided."),
            "# Context\n\n" + _list_or_default(data.context) + warnings,
            "# Relevant Code\n\n" + _code_or_default(data.code_blocks),
            "# Logs\n\n" + _list_or_default(data.logs),
            "# Reproduction\n\n" + _numbered_or_default(data.reproduction),
            "# Constraints\n\n" + _list_or_default(data.constraints),
            "# Research Goals\n\n" + _list_or_default(data.research_goals),
            "# Expected Output\n\n" + _list_or_default(data.expected_output),
        ]
    ) + "\n"
