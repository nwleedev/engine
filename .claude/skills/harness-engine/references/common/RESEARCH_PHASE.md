# Common Research Phase

## Purpose

This document defines the common research phase that `harness-engine` must perform before creating any `task_type` harness.

This phase does not replace domain-specific task adapters. Instead, it closes the following items commonly before all harness creation:

- Primary evidence source priority
- Recency verification
- Search execution safety rules
- Counter-evidence or limitation checks
- Evidence collection to separate examples from contracts
- Research inputs for project contract packet creation

Even when `research` is the final `task_type`, perform this phase first, then additionally apply `references/adapters/research.md`.

## Core Principles

1. Research recommended patterns and principles for the domain from official documentation, standards, and authoritative guidelines. These form the foundation of harness rules.
2. Current project code is a supplementary analysis target for identifying deviations from official standards. Do not use code patterns themselves as the basis for rules.
3. Do not finalize harness rules based solely on blogs, marketing copy, or curated articles.
4. Verify recency information alongside important rules.
5. If evidence has been gathered in only one direction, additionally search for counter-evidence, limitations, and failure modes.
6. Break search calls into small batches, and record key findings after each batch.

## Common Research Checklist

- Have you compiled recommended patterns for the domain from official documentation/standards
- Can you describe at least 3 primary evidence sources directly related to the current `task_type`
- Can you describe at least 3 failure modes most commonly encountered in this harness
- Have you secured at least 2 direct examples to reference when creating examples
- If recency matters for an item, have you recorded at least one of: date, version, or re-search confirmation
- Have you confirmed at least 1 counter-evidence item, limitation, or exception case

## Search Execution Safety Rules

- Limit parallel search calls in a single turn to a maximum of 3-4.
- If 5 or more are needed, split into batches.
- Limit results per search to typically 3-5.
- Immediately exclude irrelevant large results (PDFs, code files, vocab files, etc.).
- After each batch completes, record key findings in session notes (`<session_path>/notes/`) before proceeding to the next batch.

## Optional MCPs

- Tavily MCP
  - Suitable for augmenting with latest web search and source text extraction.
- Context7 MCP
  - Suitable for augmenting with library/framework documentation context.

Rules:

- Both are optional tools.
- Always re-verify final rules and citations against official documentation or actual source code.

## Output to Pass to Task Adapter / Contract Packet

Once the common research phase is complete, pass at least the following to the next stage:

- List of recommended patterns based on official documentation
- List of primary evidence sources (official documentation references)
- Recency verification information
- Failure modes or exception cases
- Anti/Good direct example candidates
- Items where the current project differs from official standards (if applicable)
- Separation notes distinguishing local evidence valid only for the current project from portable core rule candidates
- Stack/library/unconfirmed items to record in the contract packet

## Failure Signals

- Reviewing search results only once and immediately finalizing rules.
- Writing harness statements with zero primary evidence.
- Missing date or version information for rules where recency matters.
- Writing example statements definitively without evidence to support them.
- Not reviewing any counter-evidence or limitations at all.
