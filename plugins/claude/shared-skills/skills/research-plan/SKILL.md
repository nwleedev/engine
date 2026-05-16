---
name: research-plan
description: Use when a question, claim, technology choice, or decision needs a source strategy and counterevidence strategy before research begins.
metadata:
  short-description: Plan source-backed research
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/research-plan/SKILL.md -->


# Research Plan

## Purpose

Create a `Research Plan` that defines the research question, source strategy, counterevidence strategy, and stop condition before collecting sources or making a recommendation.

## Workflow

1. State the research question in a form that can be answered or narrowed.
2. Define source types by authority: official docs, standards, primary repos, release notes, model cards, papers, or reputable secondary sources.
3. Define recency requirements and version constraints.
4. Define how counterevidence, conflicts, and failure cases will be searched.
5. Define the stop condition for enough evidence or a blocked research state.
6. Route collected sources to `source-ledger`.
7. Route claims and decisions to `claim-evidence-map`.

## Development work

- Prefer official technical documentation and primary repositories for APIs, libraries, CLIs, runtimes, and cloud services.
- Capture versions, release channels, and compatibility windows before recommending implementation.
- Separate implementation-readiness research from broader product or strategy research.

## Non-development work

- Define source authority for market, strategy, policy, planning, and ideation questions.
- Include dissenting sources, stale-source checks, and source limitations in the plan.
- Stop when further research would not change the decision or when sources are insufficient.

## Output

```markdown
## Research Plan

| research_question | source_strategy | counterevidence_strategy | stop_condition |
| --- | --- | --- | --- |
|  |  |  |  |
```

## Do not

- Do not collect random sources before defining the question.
- Do not rely on secondary summaries when primary sources are available.
- Do not skip counterevidence for directional recommendations.
- Do not make implementation decisions from stale or versionless sources.
