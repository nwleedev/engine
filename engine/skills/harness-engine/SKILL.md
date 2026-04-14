---
name: harness-engine
description: "A skill that creates or enhances `.claude/skills/harness-<domain>-<name>.md` harness skills tailored to the user's work domain. The main agent handles decisions and user interaction, while sub-agents perform domain research and harness generation."
user-invocable: true
---

# Harness Engine

The purpose of this skill is to set up harness skills in `.claude/skills/harness-<domain>-<name>.md` that Claude can repeatedly reference for the user's work domain.

The main agent handles decisions, user interaction, and session management, while harness generation and validation are delegated to sub-agents.

This skill is neither a fully static rule engine nor a fully dynamic engine that researches from scratch each time. The basic structure is:

- Common research discipline: `references/common/RESEARCH_PHASE.md`
- Thin domain minimum contract: `references/adapters/<task_type>.md`
- Project-specific source of truth: session path `contract packet`
- Optional quality enrichment: `references/examples/<task_type>/*`

## When to Use

- When a harness for a new work domain doesn't exist yet
- When existing `.claude/skills/harness-<domain>-*` skills are too weak to use as practical work standards
- When anti-patterns, architecture, validation criteria, or templates need to be reinforced for a specific domain
- When the user wants to document "what should Claude reference before working in this domain"
- When creating the first project-specific work domain harness after syncing only the portable core to another project

## Quick Procedure (Main Agent)

1. Extract the purpose and work domain from the user's request.
2. First select candidate `task_type` from the representative classification set.
3. Check if existing `.claude/skills/harness-<domain>-*` skills exist.
4. If existing harness exists, first determine minimum contract compliance.
5. If minimum contract is not met, switch to reinforcement mode instead of reusing the existing harness.
6. First determine whether this task is `project-harness generation` or `engine-asset bootstrap`.
6a. **Determine harness file splitting strategy.** Follow "Harness File Splitting Strategy" in `references/OUTPUT_CONTRACT.md` to decide how many files to split this domain's harness into. Present the split proposal and grouping to the user for confirmation.
6.5. **Perform Intersection Scan.** If 1+ existing harnesses exist, detect intersections using the 3-step heuristic in `references/INTERSECTION.md`. If intersections are found, confirm authority assignment with the user and record in the contract packet's Intersection Map.
7. Perform the common `research` phase first. Simultaneously perform **Potential Intersection Discovery** to investigate ungenerated domains with high intersection probability with the current domain, and suggest to the user.
8. Load the domain task adapter and verify the stack/library combination.
9. Create or update the project-specific `contract packet` in the session path. Include **Intersection Map** and **Potential Intersection Domains** sections.
10. If Coverage gap or unknown domain, perform the common bootstrap phase and user verification, then reinforce the contract packet.
11. If optional example pack and stack seed reference exist, load them as reference materials only.
12. **Write and verify the Source Coverage Manifest (HARD GATE).** Verify all source files are mapped to at least 1 harness. If UNASSIGNED is not 0, request mapping decisions from the user and wait. If cross-cutting types exist, also write Cross-Cutting Distribution. **Verify consistency with Intersection Map intersection information.**
13. **Run the harness generation sub-agent.** Pass `intersection_map` and `intersection_directives` additionally.
14. **Run the validation sub-agent.**
14.5. **Perform Cross-Harness Validation.** Compare newly generated harness against all existing harnesses in the project. Block progress until undeclared intersections or contradictory rules are resolved (HARD GATE). If existing harnesses need updates, generate Pending Harness Update directives.
15. Reflect validation results in the contract packet first, then reinforce the harness. **If Pending Harness Updates exist, apply minimal edits to existing harnesses after user confirmation.**
16. If a new harness skill was created, update the domain harness list in `.claude/skills/use-repo-skills.md`. (Skip this step if the file doesn't exist — inject-harness.sh directly scans individual harness-*.md files, so the central catalog is optional.)
17. Update the session record (SESSION.md). **Verify that Intersection Metadata section is finalized in the new harness.**

## Pre-Work Checks

- Verify that root `AGENTS.md` (or `CLAUDE.md` if absent) has been read.
- Specifically check temporary file rules (temps path, `/tmp` prohibition).
- Check project-specific settings in `CLAUDE.md`.
- Verify the scope is closed by the user's request alone.
- Determine what skill filename (`harness-<domain>-<name>.md`) the final output will be.
- Determine harness file count and splitting criteria per "Harness File Splitting Strategy" in `references/OUTPUT_CONTRACT.md`. Default is concern-group splitting; present grouping proposal to the user for confirmation.
- Do not first consider whether to put project-specific examples or validation history into core documents. First apply the `portable core` / `project adapter` / `local evidence pack` separation principle.
- If existing harness exists, read it first and determine the reinforcement direction without overwriting.
- If only core has been synced from another project, assume this skill is the official path for creating that project's first local work domain harness.
- If the user explicitly states they are unfamiliar with the domain, first determine whether to apply `learning-mode` in parallel.
- All execution begins by applying `references/common/RESEARCH_PHASE.md` first.
- The source of truth for minimum contract is `common + thin adapter + contract packet`.
- `references/examples/<task_type>/` is read as reference-only evidence; do not copy as portable core rules.
- Even if existing harness exists, do not judge it as `reusable` if it does not meet the following minimum contract:
  - Core rules, anti-patterns, and validation criteria sections exist
  - Direct example code or direct cases relevant to the work domain exist
  - Sources and design rationale are directly included
  - Session resume order and pre-implementation checklist exist

## Work Domain Intake

Read `references/TASK_INTAKE.md` and first determine:

- Which `task_type` it is
- Whether to reuse existing harness
- Whether a new harness needs to be created
- Which document bundle is needed
- What stack/library combination needs a contract packet

Review the representative classification set as default first.

If there are 2+ practical candidates, do not auto-confirm — present options to the user and wait.

## Common Research Phase + Thin Adapter + Project Contract Packet

After `task_type` determination, first assess existing harness quality, then perform the common `research` phase and load the domain's thin adapter.

### Existing Harness Quality Assessment

If existing `.claude/skills/harness-<domain>-*` skills exist, first check:

- Do core rules, anti-patterns, and validation criteria sections all exist?
- Are there direct example code or direct cases relevant to the work domain?
- Are sources and design rationale directly in the document?
- Are session resume order and pre-implementation checklist visible?

If any of the above is no, the existing harness is judged as `exists but not reusable` and switches to reinforcement mode.

### Intersection Scan (Step 6.5)

Performed when the target project has 1+ existing `.claude/skills/harness-*.md` files. If no existing harness exists, record `intersection_map: none` and skip.

Read `references/INTERSECTION.md` and perform:

1. Scan the `Intersection Metadata` sections of existing harness files. If no metadata exists, dynamically extract concept_keywords from frontmatter (matchPatterns), rule titles, and Anti/Good case names.
2. Run the 3-step detection heuristic:
   - Step 1: File Scope Overlap — compare matchPatterns.fileGlob
   - Step 2: Concept Keyword Overlap — normalized matching of concept_keywords (intersection candidate at 2+ shared)
   - Step 3: Semantic Rule Analysis — classify relationships between shared concept rules (complementary/redundant/contradictory)
3. If intersections are found, present authority assignment proposal and request user confirmation.
4. If contradictory intersections exist, wait until the user resolves them.
5. Record the confirmed Intersection Map in the contract packet.

### Common Research Phase

All `task_type`s first apply `references/common/RESEARCH_PHASE.md`.

**Perspective-aware research dispatch**: If `HARNESS_PERSPECTIVES` is set (read from `.claude/engine.env`), dispatch multiple parallel research agents — one per perspective — using the harness-researcher agent with `Perspective: <name>` in each prompt. Synthesize their findings into the contract packet before proceeding to generation. If unset, perform research as a single pass.

The common research phase first organizes recommended patterns based on official documentation/standards.
Current project code analysis is supplementary for identifying deviations from official standards.

At this stage, close at minimum:

- Official documentation-based recommended patterns
- Primary evidence source priority
- Recency verification
- Failure modes or limitations
- Anti/Good direct case candidates
- Search execution safety rules
- **Potential Intersection Discovery**: Extract other domain keywords mentioned by the current domain in official docs, and investigate ungenerated domains with high intersection probability based on the adapter's `known_intersections` hints and project stack. Record results in the contract packet's `Potential Intersection Domains` and suggest to the user: "These domains have high intersection probability. Would you like to generate them together?" This step is a recommendation (SHOULD), not a HARD GATE.

Even if `research` is the final `task_type`, perform this phase first, then additionally apply `references/adapters/research.md`.

### When Adapter Exists

If `references/adapters/<task_type>.md` exists, load it.

Adapters provide only minimum contracts. Project-specific stack/library/quality criteria are recorded in the session path's contract packet.

If optional example packs exist, check:

- `README.md`
- `ANTI_GOOD_REFERENCE.md`
- `VALIDATION_REFERENCE.md`

These 3 are reference-only evidence, not hard gates. However, if they exist, verify they don't conflict with the adapter contract.

### Project Contract Packet Creation

All generation/reinforcement work creates a project-specific contract packet in the session path before proceeding.

- Default path: `.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md`
- If no session: `temps/contracts/<task_type>-contract.md`

The contract packet must contain at minimum:

- Official documentation-based recommended pattern summary
- Project goals and work scope
- Actual framework/library/runtime stack
- Project decisions that differ from official standards (with rationale)
- Required work axes
- Prohibited patterns
- Stack-specific required checks
- Official documentation source list
- Conservative defaults and unconfirmed items
- Whether engine follow-up is required
- **Intersection Map** (Step 6.5 result — `intersection_map: none` if no intersections)
- **Potential Intersection Domains** (Step 7 Research Phase result — `potential_intersections: none` if none)

### Coverage Gap Check

If **2 or more** of the following apply, run bootstrap supplementation:

- Cannot immediately list 3+ primary evidence sources for this project
- Cannot immediately define core metrics for this project
- Less than half of the adapter's Coverage Contract required axes are suitable for this project
- The user explicitly stated they lack knowledge about this project's domain

### Bootstrap Supplementation (When Coverage Gap Detected)

Run `references/common/BOOTSTRAP_PHASE.md` in **supplementation mode**. The main agent performs user verification (human-in-the-loop), and reflects the confirmed Coverage Contract in the contract packet.

### Official MCP Recommendations (Optional)

- Tavily MCP: Suitable for latest web search and original text extraction enrichment.
- Context7 MCP: Suitable for library/framework documentation context enrichment.
- Both are optional tools; final rules and citations are re-verified against official documentation or actual source code.

### When No Adapter Exists

1. **Matches representative classification but adapter doesn't exist yet**: Do not route to general harness generation. Switch execution path to `engine-asset bootstrap` and close the thin adapter, contract packet, and necessary stack seed assets together.
2. **Unknown domain**: Run `references/common/BOOTSTRAP_PHASE.md` in new mode. The main agent performs Role-Goal-Backstory definition and user verification, then passes confirmed content as input to the contract packet and `project-harness generation` path. Do not promote to representative classification without a separate decision.

### Stack Branching (When Applicable)

If the adapter has a stack branching section, check `references/stacks/<stack>.md`.

- Stack detection order: project AGENTS.md (or CLAUDE.md if absent) declaration → config file verification → request user selection
- Stack seed reference is a research aid. The final source of truth for generation/validation is the contract packet.
- If stack doc doesn't exist and execution path is `engine-asset bootstrap`, generate seed doc in the same turn.
- If stack doc doesn't exist and execution path is `project-harness generation`, reflect necessary rules in the current project harness and contract packet, and leave engine asset absence as `engine_followup_required: yes`.

## Portability Assessment

Before creating or reinforcing a harness, first determine where to place the content to be added:

1. `portable core`
   - Rules that would be maintained as-is in other projects
   - Entry points, workflows, prohibited patterns, completion criteria
2. `project adapter`
   - Connection points like paths, verification commands, local policies, project stack
3. `local evidence pack`
   - Dry runs, samples, past failure records specific to the current repository

Rules:

- Examples, absolute paths, and past failure history from the current repository are candidates for `local evidence pack` by default.
- Do not promote project-specific connection points to core; push them to adapter-type documents or templates.
- When reverting issues from copying harness to another project, submit a change request packet to the original harness repository.
- When encountering harness hierarchy issues in real projects, write an issue report in `.claude/sessions/<session_id>/notes/`.

## Perspective Mode (HARNESS_PERSPECTIVES)

When the `HARNESS_PERSPECTIVES` environment variable is set, dispatch sub-agents in parallel — one per perspective — at each of the three dispatch points: research, generation, and validation. If unset, dispatch a single agent (default behavior).

```bash
# Example: HARNESS_PERSPECTIVES="트리거가용성,패턴완결성,관찰가능성,enforcement일관성"
```

### Reading HARNESS_PERSPECTIVES

Before each dispatch point, check the project's `.claude/engine.env`:
1. If `HARNESS_PERSPECTIVES` is set: split by comma, create one dispatch per perspective
2. If unset or empty: single dispatch (existing behavior)

### Parallel Dispatch Pattern

When perspectives are set, dispatch ALL perspective agents in a SINGLE message (parallel, not sequential):

```text
[Message containing multiple Agent tool calls — one per perspective]

Agent 1: harness-researcher with prompt including "Perspective: 트리거가용성"
Agent 2: harness-researcher with prompt including "Perspective: 패턴완결성"
...
```

### Result Synthesis

After collecting all perspective results:
1. Merge findings: combine perspective-specific findings into one complete view
2. Apply consensus: items flagged by multiple perspectives → higher priority
3. Resolve conflicts: if perspectives produce contradictory findings, present to user
4. Final harness: the harness file itself is generated by ONE generation agent (not one per perspective). Perspectives inform the generation prompt as aggregated findings.

### When to Apply Each Dispatch

- **Research phase** (Step 7): Dispatch perspective agents to investigate the domain from different angles. Synthesize their findings into the contract packet before generation.
- **Generation phase** (Step 13): If perspectives are set, pass the synthesized perspective findings to the single generation agent prompt. The generation agent does NOT run in parallel (one harness file, one agent).
  - Exception: If perspectives reveal that different parts of the harness need depth in different areas, the generation agent prompt should include `Perspective findings: [merged summary]`
- **Validation phase** (Step 14): Dispatch perspective-focused validation agents in parallel. Each checks the harness from its perspective lens (Q1-Q5 gates mapped to perspectives).

> Note: Generation always produces ONE harness file via ONE generation agent. Perspectives affect research depth and validation breadth, not the number of output files.

## Harness Generation Sub-Agent Execution

Once user interaction is complete and all decisions are confirmed, run the harness generation sub-agent.

### Execution Settings

```text
Agent tool call:
  description: "harness generation for {domain}"
  subagent_type: general-purpose
  isolation: worktree
  run_in_background: false (foreground)
  prompt: (see prompt composition below)
```

If custom agent `.claude/agents/harness-researcher/` exists, Claude Code may auto-delegate via description matching. If auto-delegation doesn't work, use the general-purpose settings above.

### Sub-Agent Prompt Composition

```text
Read the following files and generate harness outputs.

1. Generation guidelines: .claude/skills/harness-engine/references/GENERATION.md
2. Output rules: .claude/skills/harness-engine/references/OUTPUT_CONTRACT.md

Note: Temporary files must be recorded under notes/ within the session_path. /tmp usage prohibited.

Work information:
- task_type: {task_type}
- execution_path: {project-harness generation | engine-asset bootstrap}
- common_research_path: {.claude/skills/harness-engine/references/common/RESEARCH_PHASE.md}
- adapter_path: {adapter_path or "none"}
- contract_packet_path: {.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md or temps/contracts/...}
- example_pack_path: {references/examples/<task_type>/ or "none"}
- bootstrap_phase_path: {common bootstrap phase path or "N/A"}
- bootstrap_mode: {new/supplement/none}
- coverage_contract: {coverage_contract content}
- user_decisions: {user-confirmed decisions}
- existing_harness_path: {existing harness path or "none"}
- session_path: {resolved literal path — main agent must resolve before dispatch}
- stack: {stack info or "N/A"}
- stack_reference_path: {references/stacks/<stack>.md or "none"}
- stack_required_checks: {stack required checks reflected in contract packet}
- engine_followup_required: {yes/no}
- coverage_manifest: {Source Coverage Manifest content in contract packet}
- cross_cutting_distribution: {Cross-Cutting Distribution content in contract packet or "none"}
- intersection_map: {Intersection Map content in contract packet or "none"}
- intersection_directives: {Intersection Map Resolution Directives content or "none"}
- splitting_strategy: {concern-group | consolidated | per-library}
- target_files: [{harness-<domain>-<name1>.md: content summary}, {harness-<domain>-<name2>.md: content summary}]
- harness_perspectives: {HARNESS_PERSPECTIVES value or "none" — perspectives are for research/validation; generation uses synthesized findings}
- perspective_research_summary: {merged summary from parallel research agents, or "N/A" if HARNESS_PERSPECTIVES unset}
```

### session_path Rules

The main agent must fill in `session_path` before dispatching the sub-agent.

1. If the session directory path is known from `## Session State` context (e.g., file paths in Snapshots containing `.claude/sessions/<uuid>/`), use it
2. If the session directory path is unknown, use `temps/<date>/<scope>/` instead (per project convention)
3. Do NOT generate random IDs with `uuidgen`, `mktemp`, `$RANDOM`, or similar — this creates orphan directories that the Stop hook cannot manage
4. Do NOT use `ls -td .claude/sessions/*/` to guess — in concurrent sessions it may return a different session's directory

### Sub-Agent Result Processing

Information returned by the sub-agent:

- List of generated/modified files
- Research evidence summary
- Coverage fulfillment status
- Anti/Good pair fulfillment status
- Contract packet usage status
- Optional example pack usage status
- Stack reflection status
- `engine_followup_required`
- Unfulfilled items
- worktree_path (when worktree isolation is used)
- Intersection directive fulfillment status
- Splitting strategy fulfillment status (per-file Coverage axis mapping results)

Review results; if there are unfulfilled items, report to the user and decide on response.
Do not start implementation tickets unless the verdict is `pass`.

## Validation Sub-Agent Execution

After the harness generation sub-agent completes, run the validation sub-agent.

### Execution Settings

```text
Agent tool call:
  description: "harness validation for {domain}"
  subagent_type: general-purpose
  isolation: none (no worktree — read-only)
  run_in_background: false (foreground)
  prompt: (see validation prompt below)
```

### Validation Sub-Agent Prompt

```text
Read only the harness document at the following path and perform validation.

Harness path: {worktree_path}/.claude/skills/harness-{domain}-{name}.md
Validation criteria: .claude/skills/harness-engine/references/VALIDATION.md
Temporary file rules: Record only in temps/ under session_path. /tmp usage prohibited.
session_path: {resolved literal path — main agent must resolve before dispatch}
Common research phase: {.claude/skills/harness-engine/references/common/RESEARCH_PHASE.md}
Task adapter: {adapter_path or "none"}
Project contract packet: {contract_packet_path}
Example pack: {example_pack_path or "none"}
Bootstrap phase: {bootstrap_phase_path or "N/A"}
Execution path: {project-harness generation | engine-asset bootstrap}
Stack seed reference: {stack_reference_path or "none"}

Validation method:
1. Read only the harness document and related engine references, then perform the following virtual task: {virtual task scenario}
2. Report missing information, ambiguous instructions, and conflicting rules in the harness.
3. Determine pass/fail for each item against VALIDATION.md minimum checklist, contract packet compliance, and stack-specific checks.

Report format:
- Missing items: [list]
- Ambiguous points: [list]
- Conflicting rules: [list]
- Checklist pass status: [per item]
- engine follow-up required: [yes/no]
- Overall verdict: [pass/needs reinforcement]
- Implementation start allowed: [yes/no]
```

**Perspective-aware validation dispatch**: If `HARNESS_PERSPECTIVES` is set, dispatch multiple parallel validation agents — one per perspective — using the validation prompt with `Perspective: <name>` appended. Each agent focuses on its perspective's quality gates (Q1-Q4 from VALIDATION.md Quality Gate Validation Procedures). Collect all perspective validation reports and combine into the final validation result. Any perspective that fails blocks the overall verdict.

### Validation Result Processing

- **Pass**: Maintain worktree. Report results to user. Perform discovery registration (AGENTS.md or CLAUDE.md, INDEX.md) if needed. The main agent starts implementation tickets only after saving validation artifacts to the session path.
- **Needs reinforcement**: Reflect missing/ambiguous/conflicting items from the validation report in the contract packet first, then pass to the harness generation sub-agent for re-execution. Implementation is prohibited.

## Cross-Harness Validation (Step 14.5)

After validation sub-agent (Step 14) passes, the main agent compares the newly generated harness against all existing harnesses in the project.

### Procedure

1. Collect all `.claude/skills/harness-*.md` file list in the project (excluding newly generated harness).
2. For each existing harness, run the 3-step heuristic from `references/INTERSECTION.md`:
   - Use concept_keywords if existing harness has Intersection Metadata
   - Otherwise dynamically extract from rule titles, Anti/Good case names, frontmatter
3. Classify results:
   - **Already declared intersections**: Detected in Step 6.5 and recorded in Intersection Map — verify authority assignment matches actual rule content
   - **Newly discovered intersections** (HARD GATE): Intersections missed in Step 6.5 — must update Intersection Map and get user authority confirmation
   - **Contradictory rules** (HARD GATE): Contradictory relationships — require user resolution
4. If existing harnesses need updates, generate `Pending Harness Update` directives (saved in session notes).
5. Verify Intersection Metadata is symmetrical in both harnesses.

### Result Processing

- **No intersections or all resolved**: Proceed to next step (Step 15)
- **Undeclared intersections found**: Update Intersection Map → user confirmation → regenerate harness or reinforce metadata only
- **Contradictory rules found**: Wait until user resolves. Regenerate harness after resolution
- **Pending Harness Update generated**: Report existing harness change content to user, apply after confirmation

## Session Management (Main Agent Responsibility)

Sub-agents do not update session files. The main agent handles:

- SESSION.md: Update work status, decisions, progress log
- Contract packet: Save in `.claude/sessions/<session_id>/notes/contracts/` or `temps/contracts/`
- Validation artifact: Save in `.claude/sessions/<session_id>/notes/validation/` or `temps/validation/`
- `.claude/skills/use-repo-skills.md`: Update domain harness list when new harness skill is created (only if file exists)
- If there is a request to feed back to another project, leave key fields of the change request packet in DECISIONS or RESEARCH.
- If reports collected from real projects exist, use only key fields extracted from the original as upstream judgment material.
- If the task involved a detected stack, verify that `engine_followup_required` and stack required checks are left in the validation artifact.

## Existing Harness Reuse Principles

- If the current project already has sufficient `.claude/skills/harness-<domain>-*` skills, do not create new skills.
- "Sufficient harness" means only cases that satisfy both minimum contract and validation pass.
- Reinforce only insufficient sections.
- Create new harness only when existing harness repeatedly cannot cover.
- If a new harness was created and `.claude/skills/use-repo-skills.md` exists, update the domain harness list. (Since inject-harness.sh directly scans individual files, catalog non-update doesn't block discovery.)
- When reinforcing existing harness, do not mix portable core and local evidence.

## Prohibitions

- Generating random session IDs (`uuidgen`, `mktemp`, `$RANDOM`) — creates orphan directories the Stop hook cannot manage
- Creating new directories without `task_type` determination
- Leaving final outputs only in `temps/` and terminating
- Passing unresolved matters to sub-agent before user confirmation
- Skipping the validation sub-agent
- Reusing existing harness that doesn't meet minimum contract as-is
- Proceeding with harness generation/validation without a contract packet
- Treating a representative classification without adapter as general harness generation
- Not leaving stack required checks in contract packet when a stack was detected
- Starting implementation tickets when validation result is not `pass`
- Completing with only one side of Anti/Good pairs written
- Not leaving sources in final documents and keeping evidence only in session notes
- Promoting current repository-specific examples to portable core rules
- Submitting core change requests for copy-usage issues without reproduction information

## Reference Files

- Intake criteria: `references/TASK_INTAKE.md`
- Generation guidelines (for sub-agent): `references/GENERATION.md`
- Output criteria: `references/OUTPUT_CONTRACT.md`
- Validation criteria: `references/VALIDATION.md`
- **Intersection detection/resolution criteria: `references/INTERSECTION.md`**
- Common research phase: `references/common/RESEARCH_PHASE.md`
- Domain adapters: `references/adapters/<task_type>.md`
- Common bootstrap phase: `references/common/BOOTSTRAP_PHASE.md`
- Stack seed guidelines: `references/stacks/<stack>.md`
- Example pack: `references/examples/<task_type>/*`
- Contract packet is written directly in `.claude/sessions/<session_id>/notes/contracts/`.
- Custom research agent: harness-researcher agent
