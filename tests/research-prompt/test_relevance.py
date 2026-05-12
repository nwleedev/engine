from __future__ import annotations

from pathlib import Path

from research_prompt.relevance import CandidateFile, rank_candidates


def test_rank_candidates_prioritizes_user_paths_and_stack_trace() -> None:
    candidates = [
        CandidateFile(path=Path("src/low.py"), signals={"symbol": 1}),
        CandidateFile(path=Path("src/mentioned.py"), signals={"user_path": 1}),
        CandidateFile(path=Path("src/trace.py"), signals={"stack_trace": 1}),
    ]

    ranked = rank_candidates(candidates)

    assert [item.path.as_posix() for item in ranked] == [
        "src/mentioned.py",
        "src/trace.py",
        "src/low.py",
    ]


def test_rank_candidates_combines_multiple_signals() -> None:
    candidates = [
        CandidateFile(path=Path("src/a.py"), signals={"symbol": 1}),
        CandidateFile(path=Path("src/b.py"), signals={"symbol": 1, "git_diff": 1}),
    ]

    ranked = rank_candidates(candidates)

    assert ranked[0].path == Path("src/b.py")
