# Generation (Harness Generation Sub-Agent Instructions)

## Purpose

This document contains execution instructions read by the harness-engine's harness generation sub-agent. The main agent (orchestration) passes this file path when launching the sub-agent, and the sub-agent reads this document to generate harness deliverables.

## Inputs Received by the Sub-Agent

The following information is passed from the main agent.

- `task_type`: The determined work domain
- `execution_path`: `project-harness generation` or `engine-asset bootstrap`
- `common_research_path`: Common research phase document path
- `adapter_path`: Adapter file path (or "none")
- `contract_packet_path`: Project-specific contract packet path
- `example_pack_path`: Optional example pack path (or "none")
- `bootstrap_phase_path`: Common bootstrap phase document path (or "not applicable")
- `bootstrap_mode`: `new`, `supplement`, `none`
- `coverage_contract`: User-confirmed Coverage Contract (required axes + conditional axes)
- `user_decisions`: User-confirmed selections (including bootstrap verification results)
- `existing_harness_path`: Path to existing harness if present (for reinforcement mode)
- `session_path`: Session directory path
- `stack`: Stack information (or "not applicable")
- `stack_reference_path`: Stack seed reference document path (or "none")
- `stack_required_checks`: Stack required checks recorded in the contract packet
- `engine_followup_required`: `yes` or `no`
- `coverage_manifest`: Source Coverage Manifest (source file → target harness mapping table)
- `cross_cutting_distribution`: Cross-Cutting Distribution instructions (or "none")
- `intersection_map`: Intersection Map (intersection detection results or "none")
- `intersection_directives`: Intersection Map's Resolution Directives (or "none")
- `splitting_strategy`: One of `concern-group`, `consolidated`, `per-library`
- `target_files`: List of files to generate and a content summary for each file (e.g., `[{harness-fe-architecture.md: "FSD, component boundaries, Coverage axis #5"}, {harness-fe-data-management.md: "state management, queries, forms, Coverage axes #1-#4"}]`)

## Execution Procedure

### 1. Load Common Research Phase

Read the provided `common_research_path` first and identify the following.

- Primary evidence source priority
- Freshness verification principles
- Search execution safety rules
- Counter-evidence or failure mode collection principles

This step is applied universally across all `task_type` values.

### 2. Load Thin Adapter

Read the adapter at the provided `adapter_path` and identify the following items.

- Coverage Contract minimum required axes
- Primary evidence sources
- Anti/Good minimum required pairs
- Minimum dry-run criteria

When the `execution_path` is `engine-asset bootstrap` because a representative classification has no adapter, use the `coverage_contract` and `user_decisions` provided by the main agent as the basis for the adapter draft.

### 2.5. Verify Source Coverage Manifest and Cross-Cutting Distribution

Read the provided `coverage_manifest` and verify the following:
- Whether the harness currently being generated is included in the manifest's target harnesses
- If cross-cutting sources exist, check the distribution instructions in `cross_cutting_distribution`
- Prepare to reflect cross-cutting content in the appropriate sections of the corresponding harness according to the distribution instructions

Reflection targets: core rules, anti-patterns, or validation criteria as specified in the distribution instructions.

### 2.7. Intersection Directive Processing

If the provided `intersection_directives` exist (not `"none"`), perform the following.

1. Read `references/INTERSECTION.md` to understand authority type-specific rule/example writing conventions.
2. For each intersection, check this harness's authority and determine the writing approach:
   - **primary authority**: Write full rules + full code examples for the concept. No reference marker needed.
   - **secondary authority**: Write abbreviated rules from this domain's perspective and add a Cross-Reference marker referencing the primary harness. Code examples can be delegated to the primary.
   - **shared authority**: Write full rules + full code examples from this domain's perspective and add a Cross-Reference marker referencing the other harness.
3. Pre-plan rule numbers and Anti/Good cases corresponding to intersections (apply distribution rules in Step 10).
4. Prepare `concept_keywords` and `Declared Intersections` to record in this harness's `Intersection Metadata` section.

If `intersection_directives` is `"none"`, skip this step.

### 3. Load Project Contract Packet

Read `contract_packet_path` and use this document as the generation reference point for this project.

Rules:

- The contract packet is the final source of truth for generation/validation.
- Prioritize the packet's project-specific stack/library rules over the adapter.
- If the packet has undecided items, make them visible in the document and ensure the harness does not hide that uncertainty.

### 4. Check Existing Harness

If `existing_harness_path` exists, read the existing harness and identify insufficient sections. Do not overwrite; establish a reinforcement direction.

### 5. Check Optional Example Pack

If `example_pack_path` exists, read only the necessary files.

Rules:

- This path is reference-only evidence, not an answer copy.
- The style and structure of examples can be referenced, but content unrelated to the project stack should not be copied as-is.
- Repository-specific cases are treated only as examples, not as portable core.
- Generation proceeds even if no example pack exists.
- If an example pack exists, do not include content that conflicts with the adapter or contract packet in the final harness.

### 6. Check Stack Seed Reference

If `stack_reference_path` exists, read the document and cross-check with `stack_required_checks`.

Rules:

- The stack seed reference is a research supplementary material.
- When a stack is detected, the actual reflection standard is the contract packet.
- If no seed doc exists and the `execution_path` is `engine-asset bootstrap`, the necessary seed doc can also be generated.
- If no seed doc exists and the `execution_path` is `project-harness generation`, reflect the necessary rules in the current target project harness and maintain `engine_followup_required`.

### 7. Portability Packaging Decision

Before adding content, first determine which of the following three categories it belongs to.

- `portable core`: Rules that would persist when copied to another project
- `project adapter`: Project-specific paths, validation commands, stack integration points
- `local evidence pack`: Repository-specific dry-runs, samples, validation records

Rules:

- Do not use the current repository's examples, absolute paths, or past failure history as core rules.
- If local integration points are absolutely necessary in core documents, leave them only as templates or "items to be filled in by the project."

### 8. Domain Research

Perform research applying both the common research phase and the adapter's primary evidence source rules. If the adapter does not define primary evidence sources, follow the common research phase's general-purpose order.

1. Official documentation for the domain (frameworks, libraries, standards bodies, etc.)
2. Standards documents (RFC, W3C, ISO, etc.)
3. Actual open-source code/documentation
4. Public issues and supplementary materials

Do not finalize harness rules based solely on blog evidence.

#### Research Basic Direction

Domain research fundamentally involves organizing patterns recommended by official documentation. Research the following:

1. Officially recommended patterns for the domain/framework/library
2. Defaults and recommended settings explicitly stated in official documentation
3. Anti-patterns explicitly stated in official documentation
4. Migration guide changes for the relevant framework version (when applicable)

Current project code analysis is performed supplementarily to identify deviations from official standards.
Do not use patterns found in code as the basis for rules.

The following optional MCPs can be used as supplementary tools when available.

- Tavily MCP: Supplementary latest web search and source text extraction
- Context7 MCP: Library/framework documentation context supplementation

However, MCP results must be re-verified against official documentation or actual source code.

#### Search Execution Safety Rules

- Limit parallel search calls in a single turn to a maximum of 3-4.
- If 5 or more are needed, split into batches.
- Limit max_results for each search to 3-5.
- Immediately exclude irrelevant large items from search results (PDFs, code files, vocab files, etc.).
- After each batch completes, record key findings in session notes (`<session_path>/notes/`) before proceeding to the next batch.
- If search targets span different languages/regions, separate batches by language.

#### Domain Exploration Sub-Agent Execution (Optional)

Internally launch a domain exploration sub-agent if 2 or more of the following apply.

- Cannot immediately list 3 or more primary evidence sources for this project
- Cannot immediately define the key metrics for this project
- Less than half of the adapter's Coverage Contract required axes are appropriate for this project

When launching the domain exploration sub-agent:

- subagent_type: general-purpose
- Instructions: "Please research the key work axes (at least 6), failure modes (at least 5), authoritative primary evidence sources, quality criteria used by experts, and specific cases that can be used for Anti/Good pairs for [domain]."
- Output: Coverage supplementary information + evidence sources + cases

### 9. Current Project State Supplementary Analysis

The rules based on official documentation organized in Step 8 are the base content of the harness.
In this step, supplementarily verify whether the current project differs from the official standards.
If differences exist, record them as separate supplementary items in the harness.

#### Evaluation Target Determination

Set different evaluation targets depending on the domain type.

- **Software domains** (frontend, backend, ops, security, testing, etc.): Evaluate the project's software architecture against recommended patterns (Layered, Clean, Hexagonal, FSD, etc.).
- **Research/analysis domains** (market research, competitive analysis, user research, etc.): Evaluate research methodologies against industry standard methodologies (quantitative/qualitative research, triangulation, hypothesis-verification loops, etc.).
- **Strategy/design domains** (product design, monetization strategy, business planning, etc.): Evaluate strategic frameworks against proven models (Lean Canvas, Business Model Canvas, Design Thinking, etc.).
- **Unknown domains**: If established frameworks or methodologies for the domain were identified during domain research, use those as the standard. If no established standards exist, record "evaluation criteria undetermined" in the contract packet and perform a conservative evaluation with available evidence only.

#### Procedure

1. Check the current project against the list of officially recommended patterns.
   - Use official documentation, standards, and verified projects/cases as pattern sources.
   - If the adapter defines style branching, use the style confirmed in the contract packet as the evaluation standard.
   - If no adapter exists (engine-asset bootstrap path), establish evaluation criteria from domain research and contract packet only.

2. Classify items with differences.
   - Intentional choice: The project implemented differently with justification — record with rationale as supplementary
   - Unmet: Not yet applied — supplementary record
   - Not applicable: A pattern that does not apply to this project

3. Items matching the official standard require no separate record (since harness rules are already TO-BE based).

4. Reflect supplementary analysis results in deliverables.
   - Core rules: Summary of current project state vs. official standards + project supplementary items
   - Anti-patterns: Unmet gap anti-pattern candidates + project supplementary Anti/Good pairs
   - Validation criteria: Include pattern compliance verification in criteria + project supplementary checklist

#### Rules

- The basis for harness rules is official documentation. Even if the current code follows the pattern, the basis is "officially recommended."
- Patterns unique to the current project (local conventions, project-specific helpers) are placed as supplementary items, not base harness rules.
- Do not uncritically accept the project's current structure. Describing the current state as recommended without evaluation is prohibited.
- When a project intentionally deviates from recommended patterns, record it as a conscious trade-off, not a defect, in the supplementary section.
- Pattern sources must be from primary evidence sources in the domain research, and standalone blog opinions must not be used as the basis.

### 10. Write Anti/Good Pairs

Write Anti and Good **as mandatory pairs** for all cases in the adapter's required pair list and the contract packet's project-specific required pair list.

Rules:

- Having only one side is determined as an incomplete state.
- Each pair must specify a case name so the correspondence is clear.
- For code-related domains, include bad example (code block) + recommended alternative (code block).
- For non-code domains, include bad practice (description) + recommended method (description).
- Code examples are classified into two types:
  - TO-BE examples: Code patterns from official documentation/guides. The harness's default examples.
  - Project supplementary examples: Code from the current application implementation. Added as separate supplements when needed.
- Good examples are written based on code patterns from official documentation/guides by default.
- Anti examples are written based on anti-patterns explicitly stated in official documentation by default.
- Examples taken from the current project code are distinguished with a "project supplement" label.
- Write additional pairs discovered in the contract packet beyond the adapter's minimum pairs.
- If the example pack has strong direct examples, the strength and descriptive density of patterns can be referenced from there.
- **If intersection directives exist**, apply the distribution rules from `references/INTERSECTION.md` to Anti/Good pairs corresponding to intersections:
  - primary authority → full Anti code + full Good code
  - secondary authority → abbreviated from this domain's perspective + reference to primary harness
  - shared authority → full Anti/Good pair from this perspective + mutual reference markers

### 11. Enforcement Rule Extraction (Software Domains, Optional)

Execute only for software domains when a stack is detected in the contract packet. Non-software domains skip this step.

Procedure:

1. Review the Anti/Good pairs written in Step 10 and identify **auto-detectable anti-patterns**.
   - Patterns enforceable by lint rules (e.g., unused variables, incorrect import order, prohibited API usage)
   - Patterns enforceable by static analysis (e.g., type safety, circular dependencies)

2. Research corresponding rules in the stack's lint/static analysis tools.
   - JavaScript/TypeScript: ESLint + related plugins
   - Python: Ruff, Flake8, mypy
   - Go: golangci-lint
   - If the adapter specifies enforcement tools, prioritize those.

3. Organize in `enforcement/LINT_RULES.md`. For each rule:
   - Rule name (e.g., `react-hooks/exhaustive-deps`)
   - Severity (`error` or `warn`)
   - Rationale (which anti-pattern it blocks)
   - Configuration code block (content to put in the actual configuration file)

Rules:

- The deliverable of this step is a configuration **guide document** (`.md`). Actual configuration files (`.eslintrc`, `ruff.toml`, etc.) are generated based on this document during implementation.
- Adjust rule severity according to the contract packet's `enforcement_severity` value (strict: mostly error, moderate: only core as error rest as warn, minimal: only core as warn).
- If the project already has lint configuration, do not overwrite; specify the reinforcement direction in the document.

### 12. Write Deliverables

#### 12a. Apply Splitting Strategy

Finalize the list of files to generate according to the provided `splitting_strategy` and `target_files`.

- `consolidated`: 1 file in `target_files`. Write all rules, Anti/Good pairs, and validation criteria in a single file.
- `concern-group`: 2-3 files in `target_files`. Place the designated Coverage axes and libraries in each file. Rules requiring inter-file interaction are described completely within the file of the group the rule belongs to.
- `per-library`: Per-library files in `target_files`. Write only the rules for the corresponding library in each file.

Limit each file's `matchPatterns.regex` to the libraries/concerns that file covers.

#### 12b. Generate Per-File Deliverables

Apply the writing rules below for each file in `target_files`.

Write or reinforce the harness skill at `.claude/skills/harness-<domain>-<name>.md`.

Follow the deliverable rules in `references/OUTPUT_CONTRACT.md`.

If the current work scope is `engine-asset bootstrap` or reinforcement of harness-engine's own reusable assets, the following paths can also be generated/modified.

- `references/adapters/<task_type>.md`
- `references/examples/<task_type>/README.md`
- `references/examples/<task_type>/ANTI_GOOD_REFERENCE.md`
- `references/examples/<task_type>/VALIDATION_REFERENCE.md`
- `references/stacks/<stack>.md` (when applicable)

Each final deliverable is an individual `.claude/skills/harness-<domain>-<name>.md` file (per `target_files`), containing the following sections:

- YAML frontmatter (name, description, user-invocable: true, matchPatterns)
  - description must follow the format `Use when working with X — keyword1, keyword2`
  - Include matchPatterns so the suggest-harness.sh hook can auto-suggest on file reads
  - matchPatterns.fileGlob: Target file path regex (e.g., `"^.*/src/.*\.(ts|tsx)$"`)
  - matchPatterns.regex: File content matching regex array (e.g., `- "useQuery|useMutation"`)
  - Skills based on work intent rather than code content (refactoring, UX exploration, etc.) may omit matchPatterns
- Core rules (architecture, workflows) — intersection rules include reference markers
- Anti-patterns (Anti/Good pairs) — authority-specific distribution rules applied to intersection pairs
- Validation criteria (completion conditions, checklists)
- **Intersection Metadata** — includes `concept_keywords`, `Declared Intersections`, `Potential Intersections`. Even without intersections, include `concept_keywords` and empty sections.

Minimum section contract:

- What this harness is for
- When to apply it
- What procedure to follow
- What is prohibited
- What indicates completion
- What to read when resuming a session
- Where sources and design rationale are located
- Where to place project-specific integration points
- Whether repository-specific examples are explained so they are not mistaken for core rules
- Whether stack/library rules and validation points confirmed in the contract packet are visible

### 13. Record Research Evidence

Record researched evidence in session `notes/`. Add entries to the notes/ folder under `session_path`.

## Deliverable Format

When the sub-agent completes, return the following information to the main agent.

1. **List of generated/modified files**: Paths and each file's role
2. **Execution path**: `project-harness generation` or `engine-asset bootstrap`
3. **Research evidence summary**: Primary evidence sources used and key findings
4. **Coverage fulfillment status**: Fulfillment status per adapter minimum axis and contract packet project axis
5. **Anti/Good pair fulfillment status**: Completion status per minimum pair and project pair
6. **Contract packet usage status**: Which packet was read and which items were reflected
7. **Optional example pack usage status**: Which example pack was read and what was referenced
8. **Stack reflection status**: Whether stack seed reference was used and contract packet reflection content
9. **Common phase usage status**: How the common research phase and bootstrap phase were applied
10. **engine_followup_required**: `yes/no` and reason
11. **Unfulfilled items**: Items not fulfilled during research or writing (if any)
12. **Source Coverage Manifest compliance status**: Whether manifest target harnesses match actually generated harnesses
13. **Cross-cutting distribution status**: Whether cross-cutting source distribution instructions were fulfilled and distribution log path
14. **Intersection directive fulfillment status**: For each intersection in intersection_directives, whether authority-specific rule writing conventions were followed, reference markers were included, and Intersection Metadata section was included
15. **Splitting strategy fulfillment status**: Whether all files specified in `target_files` were generated, and whether per-file Coverage axis mapping matches the specification

## Temporary File Rules

- Research intermediate deliverables, temporary notes, etc. must be recorded in the `notes/` folder under `session_path`.
- Do not use system temporary directories (`/tmp`, etc.).
- In environments without sessions, use `temps/` at the project root.

## Prohibitions

- Do not update session files (SESSION.md) (main agent's responsibility)
- Do not update `.claude/skills/use-skills.md` (main agent's responsibility)
- Do not ask questions directly to the user (main agent handles user interaction)
- Do not arbitrarily finalize generation criteria without a contract packet
- Do not omit sources from final documents
- Do not write only one side of an Anti/Good pair and mark it complete
- Do not promote local examples to portable core rules
- Do not write files to system temporary directories (`/tmp`, `/var/tmp`, etc.)
