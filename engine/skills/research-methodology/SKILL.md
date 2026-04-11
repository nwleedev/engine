---
name: research-methodology
description: "Research methodology for questions requiring investigation — technology selection, library comparison, architecture decisions, best practice verification. Used by both the project-researcher agent and inline research."
user-invocable: true
---

# Research Methodology

A methodology applied to project-level research. Used for questions requiring evidence-based answers such as technology selection, library comparison, architecture decisions, and best practice verification.

---

## General Principles

- Cross-verify answers and work rationale with internet research. Prioritize official documentation and actual source code over blogs/curated articles. Research in recency order.
- Cite reliable sources for all work.

---

## Source Priority

### Software Domain

1. Official documentation
2. Standards documents (RFC, spec)
3. Actual source code
4. Public issue trackers, vendor technical resources, supplementary materials

### Non-Software Domain

1. Academic papers, government/international organization official materials
2. Industry standard reports, professional organization publications
3. Public datasets, official statistics
4. Professional books, supplementary materials

### Prohibited

- Confirming technical conclusions based solely on blog evidence
- Treating marketing copy as technical facts — use only as usage clues
- Citing materials without date/version verification

When a blog is the only evidence: verify in official documentation, or if verification is impossible, mark as `unconfirmed`.

---

## Search Execution Safety

- Limit single-turn parallel searches to a maximum of 3-4.
- If 5+ are needed, split into batches.
- Limit results per search to 3-5.
- Immediately exclude irrelevant large results (PDFs, vocab files, etc.).
- After each batch completion, record key findings before proceeding to the next batch.
- On tool call failure (API Error 500, etc.): (1) record work from the previous turn, (2) estimate error cause, (3) halve parallel call count and retry, (4) if retry fails, present alternatives to the user.

---

## Research Checklist

All of the following must be satisfied before research is complete:

- [ ] Have at least 3 primary evidence sources directly related to the research topic been obtained?
- [ ] Can at least 3 most common failure modes/limitations be explained?
- [ ] Have at least 2 direct reference cases been obtained?
- [ ] For items where recency matters, has at least 1 of date, version, or re-search fact been recorded?
- [ ] Has at least 1 counter-evidence, limitation, or exception case been verified?

---

## Claim-to-Evidence Separation

- Record evidence notes and final conclusions separately. Do not mix them in the same paragraph.
- High-impact claims (technology selection, architecture decisions, performance assessments) require at least 2 independent evidence sources.
- If independent evidence is insufficient, mark the claim as `unconfirmed`.

---

## Contradiction Rule

- If only one-directional evidence has been gathered, additionally investigate counter-evidence, limitations, and failure modes.
- For comparative research, separately record each option's irreplaceable domains.
- Do not reach conclusions without counter-evidence.

---

## Optional MCP Tools

- **Context7 MCP**: Suitable for library/framework documentation context enrichment.
- **Tavily MCP**: Suitable for latest web search and original text extraction enrichment.

Rules:
- Both are optional. Research can be performed with WebSearch/WebFetch even if they are not installed.
- MCP results must also be re-verified against official documentation or actual source code before final citation.

---

## Failure Signals

If any of the following apply, the research is insufficient:

- Confirming conclusions after viewing search results only once.
- Writing claims with zero primary evidence sources.
- No date or version information for items where recency matters.
- No counter-evidence or limitations reviewed at all.
- Evidence notes and conclusions are mixed without separation.
