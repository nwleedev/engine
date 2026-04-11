# Cross-Domain Intersection

## Purpose

A reference document for proactively detecting rule-level intersections when 2 or more harnesses coexist in the same project, assigning authority, and consistently handling them during generation/validation.

This document is referenced in harness-engine's Step 6.5 (Intersection Scan), Step 7 (Potential Intersection Discovery), and Step 14.5 (Cross-Harness Validation).

## When to Apply

- When creating a new harness or reinforcing an existing harness
- When the target project already has 1 or more `.claude/skills/harness-*.md` files
- When identifying ungenerated domains with high intersection potential with the current domain during the Research Phase

## Detection Against Existing Harnesses (Step 6.5)

### 3-Stage Heuristic

Intersection detection is performed in 3 stages, applied sequentially starting from the lowest-cost stage. If no intersections are found at a given stage, do not proceed to the next stage.

#### Stage 1: File Scope Overlap

Check whether two harnesses cover the same file scope.

- Comparison target: frontmatter's `matchPatterns.fileGlob`
- Determination: If the two glob patterns have an overlapping file set, it is an overlap
- Non-software domains do not have fileGlob, so skip this stage

#### Stage 2: Concept Keyword Overlap

Check whether two harnesses share concepts.

- Comparison targets:
  - Existing harness's `Intersection Metadata` section's `concept_keywords` (if present)
  - If metadata is absent, dynamically extract from rule titles, Anti/Good case names
  - New harness's contract packet required axes, Anti/Good required pair list
- Normalization: Unify hyphens/underscores, split compound words (e.g., `server-only` = `server_only` = `serveronly`)
- Determination criterion: If **2 or more** shared keywords exist, classify as intersection candidate
- False positive tolerance: Since they are filtered out at the user confirmation stage, maintain high sensitivity at the detection stage

#### Stage 3: Semantic Rule Analysis

Classify the relationships of rules with shared keywords.

- **complementary**: Cover the same concept from different perspectives (WHERE vs WHY, structure vs security). Compatible.
- **redundant**: Duplicate description of identical content. Designate one as canonical and convert the other to a reference.
- **contradictory**: Conflicting directives. A HARD CONFLICT that the user must resolve.

Classification criteria:
1. If two rules have the same **target** (WHAT) and same **directive** (HOW) → redundant
2. If two rules have the same **target** (WHAT) and different **perspective** (WHY) → complementary
3. If two rules have the same **target** (WHAT) and conflicting **directive** (HOW) → contradictory

## Potential Intersection Domain Discovery (Step 7 Research Phase Integration)

During the Research Phase, investigate **ungenerated domains** with high intersection potential with the domain currently being created.

### Investigation Methods

1. **Official documentation keyword extraction**: Collect keywords from other domains mentioned in the current domain's official documentation.
   - Example: FSD documentation mentions "server-only", "security boundary" → possible security domain intersection
   - Example: Backend documentation mentions "rate limiting", "authentication" → possible security domain intersection
2. **Adapter known_intersections hints**: If the adapter has a `known_intersections` section, reference it first.
3. **Project stack-based inference**: Infer domains with high intersection potential from the current project's technology stack.
   - Example: Next.js + API routes → security (input validation, CORS)
   - Example: React + SSR → performance (hydration, bundle size)
   - Example: Prisma + DB → security (SQL injection, data projection)
4. **Existing harness potential_intersections**: If existing harnesses in the project have `Potential Intersections` metadata, check whether the current domain is mentioned there.

### Output

Record investigation results in the contract packet's `## Potential Intersection Domains` section.

```markdown
## Potential Intersection Domains

| Domain | Intersection Concepts | Evidence | Existing Harness |
|---|---|---|---|
| security | server-only, input-validation | FSD official docs security boundary section | none |
| testing | component-boundary | FSD testing guide | none |
```

### User Interaction

Present discovered potential intersection domains to the user:
- "These domains have a high likelihood of intersection. Would you like to generate them together now?"
- If the user selects, generate sequentially in the same session (after current harness completion)
- If not selected, record in the harness's `Potential Intersections` metadata for future reference

**Constraint**: This step is a recommendation (SHOULD), not a HARD GATE. Proceeding is possible even if the user ignores it.

## Authority Assignment Rules

Assign authority per intersection to determine which harness holds primary ownership of the concept.

### Assignment Order

1. The harness where the concept is in the adapter Coverage Contract's **required axes** → `primary`
2. If both adapters have it as a required axis → apply the next criteria:
   - Explicitly stated in required axes vs appearing only in Anti/Good: the side with explicit statement is primary
   - Both sides explicitly stated: `shared` (same concept from different perspectives)
3. If neither side has it as a required axis → `user-decides`

### Authority Types

| Authority | Meaning | Rule Writing Approach |
|---|---|---|
| `primary` | This harness holds the canonical rule for the concept | Write full rules + code examples |
| `secondary` | Another harness is primary | Abbreviated rules from this domain's perspective + primary reference marker |
| `shared` | Both sides cover the same concept from different perspectives | Each writes full rules from their own perspective + mutual reference markers |
| `user-decides` | Cannot be automatically determined | Present options to the user and wait |

## Reference Marker Format

Add reference markers to rules corresponding to intersections to specify the source and relationship of the rule.

### Secondary Authority Marker

```markdown
> **Cross-Reference** — This rule intersects with `harness-fe-fsd-module` Rule 7 (FSD placement of server-only code).
> Primary authority: harness-fe-fsd-module (WHERE perspective). This harness: WHY perspective.
```

### Shared Authority Marker

```markdown
> **Cross-Reference** — This rule intersects with `harness-fe-security` Rule 9 (server-only isolation in FSD shared layer).
> Authority: shared. FSD perspective: layer placement rules. Security perspective: security isolation rules.
```

## Anti/Good Pair Distribution Rules

Distribute Anti/Good pairs corresponding to intersections according to authority.

| Authority | Anti/Good Writing Approach |
|---|---|
| `primary` | Include full Anti code + full Good code |
| `secondary` | Abbreviated description from this domain's perspective + primary reference. Code examples can be delegated to primary |
| `shared` | Each side writes full Anti/Good pairs from their own domain perspective. Even if code examples are identical, both sides are maintained if perspective explanations differ |

Rules:
- `secondary` may include code examples, but if they duplicate the primary, they can be abbreviated as "see `harness-X` Case N for code examples"
- `shared` maintains both sides by default since the perspective (WHY) differs even if code examples are identical

## Intersection Map (Section within Contract Packet)

Record the detection results from Step 6.5 in the contract packet.

```markdown
## Intersection Map

### Detected Intersections

| Existing Harness | Detection Method | Shared Concepts | Relationship Type |
|---|---|---|---|
| harness-fe-fsd-module | file-scope + concept | server-only, data-projection | complementary |
| harness-fe-testing | concept | input-validation | complementary |

### Resolution Directives

#### server-only (harness-fe-fsd-module × harness-fe-security)
- Relationship: complementary
- FSD perspective: Layer placement rules for server-only code
- Security perspective: Reason for mandatory `import "server-only"` declaration
- Authority: shared
- Action: Add mutual reference markers to both harnesses. Each maintains their own perspective's rules.
- Anti/Good: Both sides maintain full pairs (perspective difference)

### User Confirmation
- [Confirmed] server-only: shared authority
- [Confirmed] data-projection: FSD primary
```

When no intersections exist:

```markdown
## Intersection Map

intersection_map: none
```

## Intersection Metadata (Embedded Section in Harness File)

Place after the validation criteria section in harness files (`.claude/skills/harness-*.md`).

```markdown
## Intersection Metadata

concept_keywords: [keyword1, keyword2, keyword3]

### Declared Intersections
- with: harness-<other-domain>-<name>
  concepts: [shared-concept-1, shared-concept-2]
  authority: {shared-concept-1: shared, shared-concept-2: this}

### Potential Intersections
- <domain>: <concept1>, <concept2>
- <domain>: <concept3>
```

### Field Descriptions

- `concept_keywords`: List of core concepts for this harness. Extracted from rule titles, Anti/Good case names, and contract packet required axes.
- `Declared Intersections`: Intersections that were actually detected and had authority assigned. `with` is the intersecting harness, `concepts` are shared concepts, `authority` is the ownership for each concept (`this`/`other`/`shared`).
- `Potential Intersections`: Potential intersection domains discovered during the Research Phase but for which harnesses have not yet been generated.

### Existing Harness Compatibility

Existing harnesses without an `Intersection Metadata` section are treated as "intersections undeclared":
1. In Step 6.5, read the harness's frontmatter (matchPatterns), rule titles, and Anti/Good case names to dynamically extract concept_keywords
2. Perform intersection detection with the extracted keywords
3. If intersections are found, generate a "Pending Harness Update" directive to add an Intersection Metadata section to the existing harness

## Cross-Harness Validation (Step 14.5)

Compare the newly generated harness against all existing harnesses in the project.

### Validation Items

1. **Declared intersection consistency**: Does the `Declared Intersections` in the Intersection Metadata match the actual rule content's authority
2. **Reference marker presence**: Do rules with secondary authority have reference markers. Do rules with shared authority have mutual reference markers.
3. **Undeclared intersection detection** (HARD GATE): Scan for new intersections using the 3-stage heuristic. If found, Intersection Metadata update required.
4. **Contradictory rule detection** (HARD GATE): If rule pairs classified as contradictory exist, user resolution required.
5. **Metadata mutual consistency**: Do `Declared Intersections` in both harnesses reference each other and is authority symmetric (if A is this, then B is other).
6. **Pending Harness Update**: If existing harnesses need updates, generate a directive.

### Failure Signals

- An intersection was detected but not declared in the Intersection Metadata
- Authority assignment and actual rule content do not match (primary but only has abbreviations)
- Declared Intersections in both harnesses are asymmetric
- A contradictory intersection was not resolved
- Reference markers are missing from rules that require them

## Non-Software Domain Handling

Non-software domains (research, marketing, design-doc, etc.) do not have file scope overlap.

- Skip Stage 1 (File Scope Overlap) and start from Stage 2 (Concept Keyword Overlap)
- concept_keywords are extracted from methodologies, frameworks, analysis techniques, etc.
  - Example: research harness keywords: [competitive-analysis, market-sizing, user-research]
  - Example: marketing harness keywords: [competitive-positioning, market-segmentation, AARRR]
  - Shared keyword: competitive → intersection candidate

## Prohibitions

- Automatically finalizing intersection detection results without reporting to the user (authority assignment requires user confirmation)
- Proceeding with harness generation without resolving contradictory intersections
- Copying the primary authority harness's rules as-is into the secondary (replace with reference markers)
- Managing Intersection Metadata in a separate file outside the harness file
- Omitting the Intersection Metadata section when no intersections exist (include concept_keywords and empty Declared Intersections and Potential Intersections subsections even without intersections)
