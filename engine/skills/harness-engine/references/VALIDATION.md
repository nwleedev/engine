# Validation

## Purpose

Verify that a harness created by `harness-engine` is in a referenceable state before actual work begins.

## Minimum Checklist

- Can explain the reason for the `task_type` determination.
- Can explain whether this execution is `project-harness generation` or `engine-asset bootstrap`.
- Can explain whether the common `research` phase was applied.
- The final deliverable exists at `.claude/skills/harness-<domain>-<name>.md`.
- Purpose, flow, prohibited patterns, and completion criteria are separated.
- If an existing harness existed, can explain why only reinforcement was done or why a new harness was created.
- If an existing harness existed, minimum contract fulfillment was assessed first, and if unmet, can explain why reuse was not chosen.
- It is clear which documents to read first when resuming a session.
- If a new `task_type` was created and `.claude/skills/use-repo-skills.md` exists, it is registered in the domain harness list.
- Sources and design rationale are directly included in the final documents.
- Can explain whether handled by the representative classification set or an exceptional new `task_type`.
- The discovery registration format does not conflict with the current `AGENTS.md` (or `CLAUDE.md` if absent) text format.
- Can explain the project contract packet path and revision status.
- The contract packet's required work axes and prohibited patterns are reflected in the deliverables.
- Repository-specific examples/paths/validation history are separated from core rules.
- Core rules include supplementary analysis of the current project against domain recommended patterns (classified as intentional choice/unmet/not applicable). Software domains evaluate architecture patterns; non-software domains evaluate methodologies/frameworks.
- Core rules are based on official documentation, and no rules exist with only project code as the sole basis.
- Project-specific items are noted as supplementary items distinct from base rules.
- Unmet gaps discovered in structure/methodology evaluation are reflected in ANTI_PATTERNS.md and VALIDATION.md.
- If a stack was detected, stack required checks are recorded in the contract packet.
- If a stack was detected, stack-specific rules are reflected in the deliverable's structure/anti-patterns/validation.
- For software domains with a detected stack, auto-detectable anti-patterns in ANTI_PATTERNS.md are mapped in `enforcement/LINT_RULES.md`.
- The `engine_followup_required` determination is appropriate and explainable.
- Can explain the storage location and minimum format of the validation artifact.
- The Source Coverage Manifest exists in the contract packet with 0 UNASSIGNED entries.
- The list of generated harness files matches the target harness column in the Manifest.
- Sources marked as cross-cutting are actually reflected in the corresponding harnesses.
- A cross-cutting distribution log exists in session notes (when cross-cutting sources exist).
- The Intersection Map exists in the contract packet (if no intersections, `intersection_map: none`).
- Potential Intersection Domains exist in the contract packet (if none, `potential_intersections: none`).
- If intersection_directives existed, authority-specific rule writing conventions were followed.
- Intersection rules include reference markers appropriate to their authority.
- The Intersection Metadata section is included in the harness file (regardless of whether intersections exist, including concept_keywords).
- Declared Intersections in the Intersection Metadata match the Intersection Map.

## Validation Sub-Agent

After the harness generation sub-agent completes, an independent instance — the validation sub-agent — performs validation against the criteria in this document.

### Role of the Validation Sub-Agent

- As an independent instance unaware of the harness generation process, it reads only the generated harness documents and contract packet to validate.
- It is separated from the agent that created the harness to prevent verification bias.
- Files generated in a worktree are accessed via worktree_path.

### Validation Procedure

1. Read the generated `.claude/skills/harness-<domain>-<name>.md` file.
2. Read the common `research` phase, task adapter, and project contract packet together.
3. If an optional example pack and stack seed reference were provided, read those additionally.
4. Verify whether the "questions" items below can be answered using only the harness and related references.
5. Check the contract packet integration verification items.
6. Attempt a hypothetical task and identify information missing from the harness.
7. Return results in the report format.

### Report Format

```text
- Missing items: [list]
- Ambiguous points: [list]
- Conflicting rules: [list]
- Checklist pass status: [per item]
- engine follow-up required: [yes/no]
- Overall determination: [pass/reinforcement needed]
- Implementation start allowed: [yes/no]
```

The main agent must save the above results as a session validation artifact in `.claude/sessions/<session_id>/notes/validation/`.

## Dry-Run Scenarios

Perform at least 1.

1. Existing harness reinforcement scenario
   - Read existing `.claude/skills/harness-<domain>-*`, assess minimum contract fulfillment first, then reinforce only insufficient sections
2. New harness generation scenario
   - Generate a document bundle for a domain not covered by existing harnesses

## Questions

- Can the next work procedure be started immediately by reading only this harness
- Even if an existing harness was weak, can the harness alone explain why immediate implementation should not proceed
- Do anti-patterns and recommended procedures not conflict with each other
- Are validation rules neither too weak nor excessive
- Can context be maintained from documents alone even after session compression
- When copying to another project, is it clear what to carry over as-is and what to recreate locally

## Contract Packet Integration Verification

When a contract packet is loaded, additionally verify the following.

- Does the contract packet exist
- Are the contract packet's project goals and work scope reflected in the harness documents
- Are all minimum Coverage Contract items from the thin adapter reflected in the harness deliverables
- Are all required axes from the contract packet reflected in the harness deliverables
- Do all minimum required Anti/Good pairs from the thin adapter exist as pairs in ANTI_PATTERNS.md
- Do all project-specific Anti/Good required pairs from the contract packet exist as pairs in ANTI_PATTERNS.md
- Do the thin adapter and contract packet not conflict with each other
- If an optional example pack exists, does it not conflict with adapter/packet contracts
- Are core rules and project adapter / local evidence not intermingled
- Is the contract packet's `architecture_pattern_evaluation` axis reflected in the core rules' supplementary analysis (software domains: architecture pattern evaluation, non-software domains: methodology/framework evaluation, intentional choice recording)
- If a stack was detected, are stack required checks reflected in core rules, anti-patterns, and validation criteria
- Even without a stack seed reference, is the contract packet for the current project sufficiently closed
- Is `engine_followup_required` appropriate

When bootstrap was used (both new mode and supplement mode), additionally verify the following.

- Is the Role-Goal-Backstory concretely defined (check for generic job title usage)
- Was human-in-the-loop verification performed (user confirmation record)
- Are items using conservative defaults explicitly noted
- **For supplement mode**: Is the existing adapter's methodology (HOW) preserved, with only project-specific domain knowledge (WHAT) supplemented

## Cross-Harness Validation Checklist (Step 14.5)

This is the cross-harness validation performed by the main agent after the validation sub-agent (Step 14) passes. Applied when the target project has 1 or more existing harnesses.

- Was the new harness compared against all existing `harness-*.md` in the project
- Does the authority assignment of declared intersections match the actual rule content (primary has full rules/code examples, secondary has reference markers)
- Are reference markers included in the correct format for rules requiring them (secondary/shared authority)
- Are Declared Intersections in both harnesses mutually symmetric (A's `this` = B's `other`)
- **Were no undeclared intersections newly discovered** (HARD GATE — if discovered, Intersection Map update required)
- **Are there no contradictory intersections** (HARD GATE — if discovered, user resolution required)
- If existing harnesses need updates, was a Pending Harness Update directive generated
- Does the new harness's Intersection Metadata include concept_keywords, Declared Intersections, and Potential Intersections

## Failure Signals

- Documents exist but the timing for application is unclear.
- The task adapter was applied without going through the common `research` phase.
- An existing harness did not meet the minimum contract but a reuse decision was made anyway.
- A harness was generated or validated without a contract packet.
- Only anti-patterns exist without recommended flows.
- Only recommended flows exist without validation criteria.
- The final deliverable exists only in `temps/`.
- A new directory was created without reading existing harnesses.
- A new `task_type` was created but the domain harness list was not updated despite `.claude/skills/use-repo-skills.md` existing.
- Sources were omitted from the final documents and evidence was left only in session notes/.
- The skill file's frontmatter (name, description, user-invocable) is missing.
- Required axes from the thin adapter's minimum Coverage Contract are missing from the harness.
- Required project axes from the contract packet are missing from the harness.
- One side (Anti only or Good only) of a required Anti/Good pair from the thin adapter or contract packet is missing.
- The optional example pack conflicts with adapter/packet contracts.
- A representative classification had no adapter but did not take the `engine-asset bootstrap` path.
- Core rules lack supplementary analysis against official standards, or uncritically accept the current project's current state.
- Rules are described with "the current code does it this way" as the sole basis, without official documentation sources.
- Project-specific local patterns are mixed with official documentation-based rules without distinction.
- A stack was detected but the contract packet has no stack required checks or they are not reflected in deliverables.
- The validation result is not `pass` but an implementation ticket was started.
- A validation artifact was not saved but an implementation ticket was started.
- The test strategy was deferred to post-implementation test alignment but the harness failed to block it.
- Repository-specific paths or examples remain as if they were mandatory rules of the portable core.
- The Intersection Map is missing from the contract packet (despite existing harnesses).
- intersection_directives existed but authority-specific writing conventions were not followed (primary has only abbreviations, or secondary lacks reference markers).
- The Intersection Metadata section is missing from the harness file.
- Declared Intersections in the Intersection Metadata do not match the Intersection Map.
- Declared Intersections in both harnesses are asymmetric (A's `this` ≠ B's `other`).
- An undeclared intersection was discovered in Cross-Harness Validation (Step 14.5) but was not resolved.
- A contradictory intersection was left unresolved when the harness was generated.
