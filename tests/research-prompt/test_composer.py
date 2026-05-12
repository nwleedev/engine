from __future__ import annotations

from research_prompt.composer import PromptInput, compose_prompt


REQUIRED_HEADINGS = [
    "# Problem",
    "# Context",
    "# Relevant Code",
    "# Logs",
    "# Reproduction",
    "# Constraints",
    "# Research Goals",
    "# Expected Output",
]


def test_compose_prompt_includes_required_sections() -> None:
    prompt = compose_prompt(
        PromptInput(
            problem="Hydration mismatch in dashboard",
            context=["Project: sample-web", "Git status: clean"],
            code_blocks=[
                {
                    "path": "src/App.tsx",
                    "reason": "user mentioned path",
                    "line_range": "10-14",
                    "excerpt": "export function App() { return <main /> }",
                }
            ],
            logs=["Warning: Text content did not match"],
            reproduction=["Run npm test", "Open /dashboard"],
            constraints=["Prefer official docs", "Do not suggest breaking changes"],
            research_goals=["Find known hydration mismatch causes"],
            expected_output=["Root cause hypotheses", "Source-backed fixes"],
            warnings=[],
        )
    )

    for heading in REQUIRED_HEADINGS:
        assert heading in prompt
    assert "src/App.tsx" in prompt
    assert "Lines: 10-14" in prompt
    assert "Warning: Text content did not match" in prompt


def test_compose_prompt_records_partial_warnings() -> None:
    prompt = compose_prompt(
        PromptInput(
            problem="CI failure",
            context=[],
            code_blocks=[],
            logs=[],
            reproduction=[],
            constraints=[],
            research_goals=[],
            expected_output=[],
            warnings=["git diff failed: exit code 129"],
        )
    )

    assert "git diff failed: exit code 129" in prompt
    assert "# Logs\n\nNot provided." in prompt
