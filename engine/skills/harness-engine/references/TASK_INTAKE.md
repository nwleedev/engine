# Task Intake

## Purpose

Consistently determine which `task_type` to assign to a user request, whether to reuse an existing harness or create a new one, and which project contract packet to close first.

## Decision Sequence

1. Check if the user has explicitly specified a work domain.
2. Review the representative classification set below to build candidates.
3. Check if existing `.claude/skills/harness-<domain>-*` harnesses exist.
4. Determine if existing harnesses can cover the request.
5. If there are 2 or more viable candidates, present options to the user and wait.
6. Only consider creating a new harness when the representative classification set cannot describe the case.
7. Determine the execution path and contract packet scope together.

## Representative Classification Set

- `frontend`
- `research`
- `backend`
- `testing`
- `security`
- `ops`
- `marketing`
- `design-doc`

Use this set as the default. Only create a new `task_type` when there is a recurring independent workflow that is difficult to describe with existing classifications.

Non-development tasks (market research, competitive analysis, marketing, design documents, business planning, etc.) and unfamiliar unknown domains are also within the scope of this engine. If a task does not fall under the representative classifications, it is routed to the **bootstrap adapter path**, which is the intended entry path for non-development tasks.

## Promotion Rules

- Do not add a new domain to the representative classification set just because it appeared once.
- Only consider promotion to the representative classification set when an exceptional `task_type` repeatedly reappears in actual work and evidence accumulates that it remains difficult to describe with existing classifications.
- Promotion decisions are made with user confirmation or within an explicit work scope.

## Pre-Scan for Intersections When Checking Existing Harnesses

When checking existing `.claude/skills/harness-*.md` harnesses (decision sequence steps 3-4), also read the `Intersection Metadata` section of each harness.

- If Intersection Metadata exists, collect `concept_keywords` and `Potential Intersections`.
- If the domain currently being created is mentioned in an existing harness's `Potential Intersections`, raise the priority of intersection detection.
- Pass the collected information as input to Step 6.5 (Intersection Scan).

## Existing Harness Reuse Signals

- A document already covering the same workflow exists.
- Minor section reinforcement is sufficient.
- Anti-patterns, validation criteria, and architecture flows can be explained within the existing framework.

Examples:

- UI development/testing-focused requests → `.claude/skills/harness-fe-*`
- Research/comparison/cross-validation-focused requests → `.claude/skills/harness-research-*`
- Market research/competitive analysis/product planning requests → `.claude/skills/harness-research-*` (product planning research section)
- Non-development tasks not covered above → bootstrap adapter path

## New Harness Creation Signals

- Existing harnesses repeatedly fail to cover the area.
- An independent workflow is required.
- Separate anti-patterns and validation criteria are continuously needed.
- High likelihood of repeated reuse in future work in the same domain.
- Cannot be naturally described by any item in the representative classification set.

## Default Priority

For composite requests, choose the leading domain in the following order.

1. Research
2. Cross-validation
3. Code writing
4. User-specified special domain

This priority is for determining the starting point of harness setup. Actual work may span multiple domains.

## Common Research Phase + Execution Path + Contract Packet Decision

After `task_type` determination, first apply `references/common/RESEARCH_PHASE.md`.

Then check whether `references/adapters/<task_type>.md` exists.

- **Adapter exists**: Proceed via the `project-harness generation` path. Load the adapter, and organize project-specific stack/library contracts in the contract packet.
- **Optional example pack exists**: Check `references/examples/<task_type>/` but treat as reference-only.
- **No adapter + representative classification**: Do not send to general harness generation. Switch to the `engine-asset bootstrap` path and generate a full set including the `.claude/skills/harness-<domain>-*` harness, thin adapter, and if needed, the example pack and stack seed document.
- **No adapter + unknown domain**: Follow the procedure in `references/common/BOOTSTRAP_PHASE.md`. The default is to generate only the local harness and contract packet via the `project-harness generation` path. Promotion to the representative classification set only happens with a separate decision.

## Project Contract Packet

All generation/reinforcement tasks must include the following contract packet decisions.

- Packet path: `.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md` or `temps/contracts/<task_type>-contract.md`
- Project stack to include in the packet
- Required work axes to include in the packet
- Prohibited patterns to include in the packet
- Stack-specific required checks
- Whether engine follow-up is needed

For domains requiring stack branching (e.g., frontend), also check `references/stacks/<stack>.md` according to the adapter's stack branching section. However, stack seed references are only supplementary materials for packet writing; the final source of truth is the packet.

## Result

The decision result must specify at minimum the following.

- `task_type`
- Whether to reuse an existing harness
- Scope of new document bundle to create
- Final deliverable path
- Execution path (`project-harness generation` / `engine-asset bootstrap`)
- Whether user confirmation was needed
- Whether handled by the representative classification set or an exceptional new `task_type`
- If an exceptional new `task_type`, whether it is a future promotion candidate
- **Whether the common research phase was applied**
- **Whether an adapter was loaded (exists/absent/bootstrap)**
- **Contract packet path**
- **Optional example pack path or absence status**
- **Whether stack branching is needed (stack name if applicable)**
- **Stack seed reference path or reason for absence**
- **Initial value of engine_followup_required**
- **Summary of existing harness Intersection Metadata** (collected concept_keywords and Potential Intersections)
- **Initial splitting strategy** (concern-group / consolidated / per-library, based on existing harness file count and project stack complexity)
