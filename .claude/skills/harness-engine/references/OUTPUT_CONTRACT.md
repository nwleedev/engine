# Output Contract

## Purpose

Separate the final deliverables and temporary deliverables of `harness-engine` tasks, and define which skill files should remain under `.claude/skills/`.

## Path Rules

- Final deliverables: `.claude/skills/harness-<domain>-<name>.md` (single skill file per harness. Multiple harnesses within the same domain are allowed when using concern-group splitting — see "Harness File Splitting Strategy" section)
- Temporary notes: `.claude/sessions/<session_id>/notes/*`
- Project contract packet: `.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md`
- Skill self-reinforcement instructions: `.claude/skills/harness-engine/**`
- Common phase documents: `.claude/skills/harness-engine/references/common/*.md`
- Task adapter: `.claude/skills/harness-engine/references/adapters/<task_type>.md`
- Skill internal reference examples: `.claude/skills/harness-engine/references/examples/<task_type>/*`
- Stack seed instructions: `.claude/skills/harness-engine/references/stacks/<stack>.md`
- When creating a new harness skill, update the domain harness list if `.claude/skills/use-repo-skills.md` exists

In environments without sessions, use `temps/contracts/<task_type>-contract.md`.

## Execution Path Rules

Generation tasks by `harness-engine` are classified into one of the following two.

1. `project-harness generation`
   - The general path for generating/reinforcing `.claude/skills/harness-<domain>-<name>.md` for the target project
   - Used when an existing adapter exists, or when setting up only a local harness first for non-representative classification/unknown domains
   - A contract packet is required even on this path
2. `engine-asset bootstrap`
   - The path for closing engine assets and the target project harness at once when a representative classification has no adapter
   - Can generate a thin adapter, and if needed, an example pack and stack seed doc alongside `.claude/skills/harness-<domain>-<name>.md`

When a representative classification has no adapter, do not process it via the general path.

## Portability Packaging Rules

Harness deliverables should distinguish the following 3 layers as much as possible.

1. `portable core`
   - Rules that would persist when copied to another project
2. `project adapter`
   - Current project's paths, validation commands, stack integration points
3. `local evidence pack`
   - Repository-specific samples, dry-runs, past validation records

Rules:

- Do not write the current repository's examples and validation history as mandatory rules of the core document.
- Push paths/commands/examples specific to a single repository into the adapter or evidence.
- When creating a new harness that needs a project adapter or local evidence, separate them into templates or guidance sections.
- Skill internal reference examples are used only as research and document structure reference materials, and are not promoted to mandatory rules of the final deliverable.
- Project-specific detailed stack/library rules are recorded first in the contract packet rather than core documents.

## Harness File Splitting Strategy

Determine how many harness files to generate for a single domain based on the following criteria.

### Default: Concern-Group Splitting

Group libraries/technologies within the same domain into 2-3 groups based on **interaction frequency and concern boundaries**. Each group becomes a `harness-<domain>-<name>.md` file.

Grouping criteria:

- Libraries with directly connected data flows are placed in the same group (e.g., query library + state management + form library → data management group)
- Structural concerns (architecture, layers, routing) are separated into a distinct group
- Libraries belonging to the same axis based on the adapter's Coverage Contract required axes are placed in the same group

### Splitting Decision Criteria (3 types)

1. **Intersection cost**: N harness files within a domain produce N*(N-1)/2 pairs of intersection checks. Files sharing the same fileGlob trigger Stage 1 (File Scope Overlap) for all pairs, progressing to Stages 2/3. If there are 4 or more files within a domain, intersection cost becomes excessive.
2. **Context efficiency**: Minimize the ratio of rules unrelated to the current task being loaded together. If a single file is repeatedly activated in different task contexts, consider splitting.
3. **Concern consistency**: If a single complete workflow (e.g., mutation → form reset → query invalidation → re-render) is described across multiple files, each file only sees part of the flow, degrading quality. Libraries with frequent interaction are placed in the same file.

### Strategy Selection Conditions

| Strategy | Application Conditions |
|---|---|
| Concern-group (default) | Most software/non-software domains. 2+ libraries with existing interactions |
| Consolidated (single file) | Non-software domains, or total rules including Anti/Good pairs under 50, or only 1-2 libraries used |
| Per-library splitting | Only when libraries have no shared concepts and are completely independent. Libraries sharing the same fileGlob should not use this strategy |

### Examples

Frontend (React + Next.js + TanStack Query + Zustand + React Hook Form):

```text
harness-fe-architecture.md
  ├ FSD layer structure, component boundaries, routing patterns
  ├ Server/Client Component boundaries, import rules
  └ Coverage axis: #5 (component/layer boundaries)

harness-fe-data-management.md
  ├ State management classification (server/route/form/global/local)
  ├ TanStack Query + Zustand + React Hook Form + useEffect
  └ Coverage axes: #1, #2, #3, #4
```

Research domain:

```text
harness-research-methodology.md (consolidated — research is inherently integrative)
```

Or when large in scale:

```text
harness-research-quantitative.md (quantitative research: market sizing, statistics, data collection)
harness-research-qualitative.md (qualitative research: interviews, user research, competitive analysis)
```

### Integration with Existing Mechanisms

- **Source Coverage Manifest**: Each split file appears in the manifest's target harness column. Cross-cutting sources are mapped to multiple files.
- **Intersection Detection (Step 6.5, 14.5)**: Concern-group splitting is designed to minimize intra-domain intersections, but if inter-group intersections occur, follow the standard intersection procedure.
- **matchPatterns**: Limit each file's `regex` to the libraries within its group to prevent unnecessary harness suggestions.

### Prohibitions

- Using per-library 1:1 splitting as the default (excessive intersection detection cost)
- Splitting files without considering intersection detection cost (number of intra-domain pairs)
- Splitting where a single complete workflow is described across 3 or more files
- Splitting libraries that share the same fileGlob into separate files without intersection resolution

## Discovery Registration Format

- When registering in `AGENTS.md` (or `CLAUDE.md` if absent), follow the section-based descriptive format used by the current document.
- If a new harness naturally fits under an existing broad category, add it to the reference document list under that category.
- If it cannot be described by existing broad categories, add a new section in the same tone as the current `AGENTS.md` (or `CLAUDE.md` if absent).
- If `.claude/skills/use-repo-skills.md` exists, add the new harness to the domain harness list. (Skip this step if the file does not exist.)

## Final Deliverable Format

Each harness is generated as an **individual `.claude/skills/harness-<domain>-<name>.md` skill file**. When using concern-group splitting, multiple files may be generated for the same domain (see "Harness File Splitting Strategy" section).

Required sections to include in the file:
- YAML frontmatter (name, description, user-invocable: true, matchPatterns)
- Core rules (architecture, workflows)
- Anti-patterns (Anti/Good pairs)
- Validation criteria (completion conditions, checklists)

Optional sections:
- Enforcement guide (lint, static analysis rule mapping)
- Combination patterns (integration with other libraries)
- Intersection Metadata (intersection metadata — recommended regardless of whether intersections exist)

When creating or substantially reinforcing a formal adapter, additionally:

- `references/adapters/<task_type>.md`
- `references/examples/<task_type>/README.md`
- `references/examples/<task_type>/ANTI_GOOD_REFERENCE.md`
- `references/examples/<task_type>/VALIDATION_REFERENCE.md`

## Section Roles Within a Single Skill File

Each harness skill file (`.claude/skills/harness-<domain>-<name>.md`) is self-contained and includes the following sections:

- **frontmatter** (required)
  - name, description, user-invocable: true
  - description describes auto-activation trigger conditions in "Use when..." format
  - `matchPatterns` (recommended): Matching rules for the suggest-harness.sh hook to auto-suggest on file reads
    - `fileGlob`: File path filter regex (optional). Files that don't match are skipped
      - Frontend: `"^.*/src/.*\.(ts|tsx)$"`
      - Backend Python: `"^.*/src/.*\.py$"`
      - Tests: `"^.*\.(test|spec)\.(ts|tsx)$"`
      - FSD layers: `"^.*/src/(app|pages|widgets|features|entities|shared)/.*"`
    - `regex`: File content matching regex array. If any match, the harness is suggested
      - Example: `- "useQuery|useMutation|queryClient"`
    - If matchPatterns is absent, fallback matching uses keywords after `— ` in the description
    - description must follow the format `Use when working with X — keyword1, keyword2` (fallback compatible)
- **Core rules** (required)
  - Official documentation/standard-based rules: Workflows, hierarchies, and patterns recommended by official documentation. Each rule cites its official documentation source
    - Software domains: Workflows, hierarchies, separation of concerns, design rationale
    - Non-software domains: Work structure, methodology, procedural flow, design rationale
  - Current project supplement (when applicable): Project-specific decisions that differ from official standards. Noted separately with rationale
- **Anti-patterns** (required)
  - Patterns to avoid, blocking rules, and source rationale
  - Must be written as Anti/Good pairs
- **Validation criteria** (required)
  - Completion criteria, validation checklists, validation rationale
- **Enforcement guide** (optional, software domains)
  - Lint/static analysis rule mappings for auto-detectable items among anti-patterns
- **Combination patterns** (optional)
  - Integration patterns with other libraries (when applicable)

## Minimum Section Contract

The final document bundle must reveal the following information.

- What this harness is for
- When to apply it
- What procedure to follow
- What is prohibited
- What indicates completion
- What to read when resuming a session
- Where sources and design rationale are located
- How project-specific integration points are separated from core
- How the project stack and validation points confirmed in the contract packet are reflected
- How the project's structure/methodology fulfills/does not fulfill domain recommended patterns, and whether intentional deviations exist
- Whether core rules are based on official documentation, with project-specific items separated as supplements
- Whether each rule has an official documentation source
- Whether items where the project implements differently from official standards are recorded as supplements with rationale

## Anti/Good Pair Completeness Rules

- For all cases in the adapter's minimum Anti/Good required pair list, both Anti and Good **must** exist in ANTI_PATTERNS.md.
- All project-specific Anti/Good required pairs defined by the contract packet must also exist.
- Having only one side (Anti only or Good only) determines the deliverable as incomplete.
- Each pair must specify a case name so the correspondence between Anti and Good is clear.

## Example Pack Rules

- The example pack is an optional engine-internal reference asset.
- The example pack does not replace the adapter's normative contracts or the contract packet.
- The generation/validation path must be viable even without an example pack.
- If an example pack exists, it must not conflict with the adapter or contract packet.
- The example pack is not synced to the target project's runtime documents.

## Contract Packet Rules

- All generation/reinforcement/validation tasks are based on the contract packet.
- The contract packet is a session deliverable, but it is the standard source of truth for generation/validation of this project.
- The thin adapter provides a minimum floor, and the contract packet closes the actual project stack/library combination.
- The validator must leave the contract packet path, revision, and engine follow-up necessity in the artifact.

### Source Coverage Manifest (Required Contract Packet Section)

The contract packet must include a Source Coverage Manifest. This section tracks that all source materials are mapped to harnesses without omission.

Format:

```markdown
## Source Coverage Manifest

| Source File | Target Harness | Type |
|---|---|---|
| STATE_MANAGEMENT.md | harness-fe-zustand | direct |
| REFACTORING.md | harness-fe-testing, harness-fe-fsd | cross-cutting |
| UX_REVIEW.md | harness-fe-fsd, harness-fe-react-hook-form | cross-cutting |

UNASSIGNED count: 0
```

Rules:
- Every source file must be mapped to at least 1 harness.
- Type is `direct` (1:1 mapping) or `cross-cutting` (1:N mapping).
- If even 1 `UNASSIGNED` item exists, generation sub-agent execution is prohibited (HARD GATE).
- Cross-cutting sources must be accompanied by a Cross-Cutting Distribution section.

### Cross-Cutting Distribution (Required Contract Packet Section, When Cross-Cutting Exists)

If the Source Coverage Manifest has `cross-cutting` types, distribution instructions must be written for each cross-cutting source.

Format:

```markdown
## Cross-Cutting Distribution

### REFACTORING.md
- Targets: harness-fe-testing, harness-fe-fsd
- Distribution method: Add refactoring safety checklist to each harness's validation criteria
- Distribution content: rename/move safety rules, reference integrity verification procedures

### UX_REVIEW.md
- Targets: harness-fe-fsd, harness-fe-react-hook-form
- Distribution method: Add UX consistency criteria to validation criteria
- Distribution content: Dynamic field UX standards, accessibility checklist
```

Rules:
- Specify targets, distribution method, and distribution content for each cross-cutting source.
- The generation sub-agent reflects content in each target harness according to these instructions.
- After reflection, record a distribution log in session notes.

### Intersection Map (Required Contract Packet Section)

When the target project has 1 or more existing harnesses, record the results of Step 6.5 (Intersection Scan). If no intersections exist, state `intersection_map: none`.

Format:

```markdown
## Intersection Map

### Detected Intersections

| Existing Harness | Detection Method | Shared Concepts | Relationship Type |
|---|---|---|---|
| harness-fe-fsd-module | file-scope + concept | server-only, data-projection | complementary |

### Resolution Directives

#### server-only (harness-fe-fsd-module × harness-fe-security)
- Relationship: complementary
- FSD perspective: Layer placement rules for server-only code
- Security perspective: Reason for mandatory `import "server-only"` declaration
- Authority: shared
- Action: Add mutual reference markers to both harnesses
- Anti/Good: Both sides maintain full pairs

### User Confirmation
- [Confirmed] server-only: shared authority
```

When no intersections exist:

```markdown
## Intersection Map

intersection_map: none
```

Rules:
- If no existing harnesses exist, write this section itself as `intersection_map: none`.
- If intersections exist, Resolution Directives and User Confirmation must be included.
- Authority assignment criteria follow `references/INTERSECTION.md`.

### Potential Intersection Domains (Required Contract Packet Section)

Record potential intersection domains discovered in Step 7 (Research Phase).

Format:

```markdown
## Potential Intersection Domains

| Domain | Intersection Concepts | Evidence | Existing Harness |
|---|---|---|---|
| security | server-only, input-validation | FSD official docs security boundary section | none |
| testing | component-boundary | FSD testing guide | none |
```

When no potential intersection domains exist:

```markdown
## Potential Intersection Domains

potential_intersections: none
```

Rules:
- This section is a recommendation (SHOULD), not a HARD GATE. Even if potential intersection domains exist, they do not block progress.
- Domains the user chooses to generate together are sequentially generated after the current harness is complete.
- Domains the user does not select are recorded as `Potential Intersections` in the harness's Intersection Metadata.

## Reference Marker Format

Add reference markers to rules corresponding to intersections. Detailed format follows `references/INTERSECTION.md`.

Secondary authority marker:

```markdown
> **Cross-Reference** — This rule intersects with `harness-X` Rule N (rule title).
> Primary authority: harness-X (perspective). This harness: (perspective).
```

Shared authority marker:

```markdown
> **Cross-Reference** — This rule intersects with `harness-X` Rule N (rule title).
> Authority: shared. X perspective: (description). Y perspective: (description).
```

## Intersection Metadata (Embedded Section in Harness File)

Place a `## Intersection Metadata` section after the validation criteria in harness files (`.claude/skills/harness-*.md`). This section provides cross-session intersection persistence without a separate Registry file.

Format:

```markdown
## Intersection Metadata

concept_keywords: [keyword1, keyword2, keyword3]

### Declared Intersections
- with: harness-<other-domain>-<name>
  concepts: [shared-concept-1, shared-concept-2]
  authority: {shared-concept-1: shared, shared-concept-2: this}

### Potential Intersections
- <domain>: <concept1>, <concept2>
```

Rules:
- Even without intersections, include `concept_keywords` and empty `Declared Intersections` and `Potential Intersections` sections.
- `concept_keywords` are automatically extracted from rule titles, Anti/Good case names, and contract packet required axes.
- In `authority`, `this` means this harness is primary, `other` means the other harness is primary, `shared` means both are equal.
- `Declared Intersections` in both harnesses must be mutually symmetric (A's `this` = B's `other`).

## Pending Harness Update (Session Notes Deliverable)

A directive generated when existing harnesses need updates during Cross-Harness Validation (Step 14.5).

Path: `.claude/sessions/<session_id>/notes/pending-harness-updates.md`

Format:

```markdown
# Pending Harness Updates

## harness-fe-fsd-module (existing)
- Change type: Add Intersection Metadata
- Added content:
  - Add harness-fe-security entry to Declared Intersections
  - Add missing keywords to concept_keywords
- Reference markers: Add shared authority marker to Rule 7
- Re-validation needed: No (metadata addition only)

## harness-fe-nextjs-appdir (existing)
- Change type: Anti/Good redistribution
- Change content: Migrate Case 10 code examples to harness-fe-fsd-module, replace with reference marker
- Re-validation needed: Yes (rule content changed)
```

Rules:
- Pending Harness Updates are not automatically applied. Apply after user confirmation.
- Changes requiring re-validation recommend re-running the existing harness's validation sub-agent.
- After application, record an application log in session notes.

## Code Example Rules

- Code examples are presented as Markdown code blocks.
- Code examples are based on official documentation/guides (TO-BE) by default.
- Examples taken from the current project's implementation code are added as supplements when needed, distinguished with a "project supplement" label.
- Do not directly create source code files for example purposes.
- If an example is tied to a specific framework or tool, include its prerequisites.

## Adapter Integration Rules

- All harness generation first applies the common `research` phase.
- When generating a harness, all minimum Coverage Contract items from the domain adapter must be reflected in the deliverables.
- The contract packet's project-specific required work axes and prohibited patterns must be reflected in the deliverables.
- The adapter's defined primary evidence sources are reflected in the deliverable's source system.
- If a representative classification has no adapter, switch to the `engine-asset bootstrap` path to generate the adapter file and, if needed, the example pack and stack seed doc together.
- If a stack seed reference exists, reference it, but fix the deliverable's final standard to the contract packet.

## Sub-Agent Deliverable Rules

- Sub-agents on the `project-harness generation` path generate/modify `.claude/skills/harness-<domain>-<name>.md` files.
- If on the `engine-asset bootstrap` path or the current task is reinforcement of harness-engine's own reusable assets, `references/adapters/<task_type>.md`, `references/examples/<task_type>/*`, `references/stacks/<stack>.md`, and `references/common/*.md` can also be generated/modified.
- Session files (SESSION.md) are not updated by the sub-agent (main agent's responsibility).
- `.claude/skills/use-skills.md` is not updated by the sub-agent (main agent's responsibility).
- When using worktree isolation, deliverables are generated in the worktree's `.claude/skills/` path.
- Upon completion, the sub-agent reports the list of generated/modified files, execution path, Coverage fulfillment status, Anti/Good pair fulfillment status, contract packet usage status, engine follow-up necessity, unfulfilled items, and **intersection directive fulfillment status**.

## Feedback Packet Rules

When rolling back harness change requests from a copied project, the following fields are required.

- source project
- copied artifact scope
- failure or friction
- expected behavior
- reproduction task
- local constraint
- proposed generalization
- evidence

Core change requests are not promoted without reproduction information and generalization judgment.

## Real Project Report Template

To enable harnesses to be copied and used in other projects, maintain the following template as a standard appendix of the portable core.

Reports are written directly in `.claude/sessions/<session_id>/notes/`.

Roles:

- Immediately create a structured report when a harness layer issue occurs in a real project.
- The contract packet serves as a temporary source of truth for organizing project-specific stack/library contracts.
- The validation report serves as a session deliverable recording harness validation pass status and implementation start permission.
- The validation artifact also records whether this execution was `project-harness generation` or `engine-asset bootstrap`, and whether `engine_followup_required` exists.

## Combination Rules with General-Purpose Agents

Harness skills are not used alone but combined with general-purpose agents to perform domain-specific operations. Do not create dedicated domain-specific agents when generating harnesses.

### Role Division Between Skills and Agents

- **Skills** = Domain knowledge (what needs to be known): Core rules, anti-patterns, validation criteria
- **Agents** = Application methods (how to apply): Review, learning, research flows

### Combination Patterns

| Stage | Agent | Harness Skill Usage |
|---|---|---|
| Pre-learning | `domain-professor` | Harness core rules → curriculum, anti-patterns → learning materials, validation criteria → completion criteria |
| During work | Claude (main agent) | Activated via description matching or `/harness-*` to reference rules |
| Post-work | `work-reviewer` | Harness anti-patterns → violation verification, validation criteria → checklist pass determination |

### Considerations When Writing Harness Deliverables

When writing harness skills, assume that general-purpose agents will dynamically read and utilize them:
- Anti/Good pairs in anti-patterns should be specific enough for work-reviewer to mechanically determine violations.
- Validation criteria checklists should be written clearly enough for per-item pass/fail determination.
- Core rules should be divided into independent concept units that domain-professor can convert into learning Units.
