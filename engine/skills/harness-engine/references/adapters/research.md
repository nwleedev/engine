# Research Task Adapter

## Purpose

When harness-engine generates or augments a research domain harness, this adapter is additionally applied after the common `research` phase to enforce the **minimum contract** specific to the research task_type.

The common `research` phase is applied first to all task_types. This document defines the additional lower bound needed when the final `task_type` is `research`.

## Coverage Contract

A research harness must include the following items. If any are missing, the harness is deemed incomplete.

### Required Axes (All Research Projects)

1. **Coverage Contract Definition**
   - Common axes to review for each research topic (minimum 4)
   - Rules for defining domain-specific extended axes
   - Minimum number of comparison axes for comparative research
2. **Perspective Matrix**
   - A perspective system in the form of a default candidate pool rather than a fixed list
   - Rules for selecting perspectives per topic
   - Branching criteria for software/non-software
3. **Source Fallback Rule**
   - Priority system for primary evidence sources
   - Rule prohibiting blog-only evidence
   - Rule for handling marketing copy
   - Obligation to verify recency
4. **Claim-to-Evidence Map**
   - Rules for separating and recording evidence per claim
   - Independent evidence requirement for high-impact claims (2 or more)
   - Rules for separating evidence notes from conclusions
5. **Question-to-Evidence Budget**
   - Minimum evidence budget per key question (primary evidence + supplementary + recency)
   - Handling rules when official documentation is absent
   - Marking rules when requirements are unmet
6. **Contradiction Rule**
   - Rule requiring mandatory recording of counter-evidence
   - Recording of potential misjudgment per axis in comparative research
   - Rule for separating non-substitutable areas

### Items That Must Be Investigated in the Project Contract Packet

- Comparison axes or judgment axes appropriate for the research topic
- Recency-sensitive items
- Primary evidence source bundles per topic
- Conditions under which results should be left as undetermined

## Primary Evidence Sources

Source Fallback Rule for research harnesses:

1. Official documentation
2. Standards documentation
3. Actual source code
4. Public issue trackers, vendor technical materials, supplementary materials

For non-software domains:

1. Academic papers, government/international organization official materials
2. Industry standard reports, materials published by professional organizations
3. Public datasets, official statistics
4. Professional books, supplementary materials

## Optional Example Pack

The research task adapter may reference the following example packs.

- `references/examples/research/README.md`
- `references/examples/research/ANTI_GOOD_REFERENCE.md`
- `references/examples/research/VALIDATION_REFERENCE.md`

Rules:

- Example packs are reference-only evidence, not normative contracts.
- The adapter itself is valid even without example packs.
- The common `research` phase closes the baseline research quality, and this adapter closes the minimum deliverable requirements for the `research` task_type.

## Anti/Good Minimum Required Pair List

The research harness's ANTI_PATTERNS.md **must** contain both Anti and Good pairs for each of the following cases.

### Source Management

| Case | Anti Content | Good Content |
|---|---|---|
| Blog-only evidence | Confirming a technical conclusion based on a single blog post | Verifying with official documentation and using blogs only as supplementary |
| Marketing copy citation | Treating product marketing copy as technical fact | Using marketing copy only as a usage clue; basing technical conclusions on official documentation |
| Recency unverified | Citing materials without date verification | Including publication/modification date, version, and current-time re-search |

### Research Breadth

| Case | Anti Content | Good Content |
|---|---|---|
| Single search termination | Drawing conclusions from first search results only | Applying the Exploration Expansion Rule, expanding perspectives |
| Biased conclusion | Collecting evidence in only one direction | Applying the Contradiction Rule, mandatory recording of counter-evidence |
| Conclusion-evidence mixing | Writing evidence notes and final conclusions in the same paragraph | Separating records using the Claim-to-Evidence Map |

### Search Execution

| Case | Anti Content | Good Content |
|---|---|---|
| Bulk search single-turn concentration | Running 5+ searches in parallel in a single turn | Executing in batches of 3-4, recording a summary per batch |
| Ignoring irrelevant results | Keeping all search results in context without filtering | Immediately excluding irrelevant large results, citing only relevant items |

### Deliverables

| Case | Anti Content | Good Content |
|---|---|---|
| Forced template flattening | Distorting research content to fit a template | Flexibly structuring with template selection sections |
| Source omission | Leaving only conclusions without citing sources | Including sources and design rationale directly in the final document |

## Dry-Run Input/Output Examples

### Positive Case: Coverage Contract Application Verification

**Input**: "Please conduct a comparative study of React state management libraries."

**Expected Output (direction the harness should guide)**:

- Define at least 2 comparison axes
- At least 1 line on potential misjudgment per comparison axis
- Apply Source Fallback Rule
- Apply Question-to-Evidence Budget

### Negative Case: Source Management Violation Detection

**Input**: A research result where the conclusion "X is the fastest" is supported by only one blog post.

**Expected Output (pattern the harness should block)**:

- Blog-only evidence -> detected as anti-pattern
- Require marking as `undetermined` or `further investigation needed`
- Require supplementation with official benchmarks or independent evidence

## Non-Software Domain Extension

When the research subject is not software:

- Select domain-appropriate perspectives instead of software-specific perspectives in the Perspective Matrix.
- In the Source Fallback Rule, substitute with "official documentation -> academic materials -> public data -> supplementary materials."
- If domain-specific Coverage axes cannot be explained by the existing framework, first perform the role definition procedure from `references/common/BOOTSTRAP_PHASE.md`.

## Design Rationale

- Coverage Contract, Perspective Matrix, Source Fallback Rule: based on legacy research harness analysis
- Anti/Good required pair structure: OpenAI GPT-5 Prompting Guide + Anthropic eval framework
- Contradiction Rule, Claim-to-Evidence Map: cross-verification system from legacy research harnesses
