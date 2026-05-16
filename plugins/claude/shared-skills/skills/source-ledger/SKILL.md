---
name: source-ledger
description: Use when research, planning, review, or decision work needs a traceable ledger of sources, authority, recency, supported claims, and limitations.
metadata:
  short-description: Track sources and limitations
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/source-ledger/SKILL.md -->


# Source Ledger

## Purpose

Create a `Source Ledger` that records source authority, recency, supported claims, and limitations so later claims can be mapped to evidence.

## Workflow

1. Assign stable source IDs using `SRC-001`, `SRC-002`, and increasing numbers.
2. Record source type, title or artifact name, URL or local path, publisher or owner, and access date when relevant.
3. Classify authority as primary, official, standard, peer-reviewed, reputable secondary, local project artifact, or low-authority.
4. Record recency, version, release date, commit, or last-updated signal when available.
5. List the claims each source supports and the limits of that support.
6. Record conflicts, missing details, paywalls, access limits, and stale-source risks.
7. Route sourced claims to `claim-evidence-map`.

## Development work

- Prefer official docs, standards, release notes, source repositories, and local code over blog summaries.
- Record library, runtime, API, schema, or CLI versions where behavior may change.
- Include local files and tests as sources when they define repository behavior.

## Non-development work

- Include source perspective, incentive, publication context, and freshness limitations.
- Separate evidence for factual claims from evidence for recommendations.
- Keep unsupported or anecdotal material out of high-confidence decisions.

## Output

```markdown
## Source Ledger

| source_id | source_type | authority | recency | claims_supported | limitations |
| --- | --- | --- | --- | --- | --- |
| SRC-001 |  |  |  |  |  |
```

## Do not

- Do not cite a source without recording what claim it supports.
- Do not treat source freshness as irrelevant for changing tools, APIs, laws, prices, or policies.
- Do not hide source limitations when they affect confidence.
- Do not let low-authority sources override primary sources without explanation.
