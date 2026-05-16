from __future__ import annotations

from pathlib import Path

from research_prompt.snippets import extract_excerpt


def test_extract_excerpt_prefers_line_window_over_file_start(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text(
        "\n".join(
            [
                "def unrelated():",
                "    return 'noise'",
                "",
                "def target():",
                "    first = 1",
                "    second = 2",
                "    return first + second",
                "",
                "def later():",
                "    return 'more noise'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    excerpt = extract_excerpt(source, line=5, context_lines=1, max_chars=2000)

    assert "def target():" in excerpt
    assert "second = 2" in excerpt
    assert "def unrelated():" not in excerpt
    assert "def later():" not in excerpt
