# Frontend Adapter

## Purpose

When harness-engine generates or augments a frontend domain harness, this adapter is loaded after the common `research` phase to apply the **minimum contract** specific to the frontend domain.

This document defines the lower bound common to all frontend projects. The actual detailed stack combinations for a given project are finalized in the session contract packet.

## Coverage Contract

A frontend harness must include the following items. If any are missing, the harness is deemed incomplete.

### Required Axes (All Frontend Projects)

1. **State Management Classification Criteria**
   - Criteria for distinguishing server state, route entry data, form state, global UI state, and local UI state
   - Tool selection rules for each state type
2. **Data Entry/Mutation Rules**
   - Data fetch entry point rules
   - Post-mutation invalidate/revalidate rules
   - Cache responsibility separation
3. **Form Handling Rules**
   - Single source of truth for form state
   - Initial value injection strategy
   - Validation entry point
4. **Side Effect (useEffect) Usage Criteria**
   - Clear classification of allowed and prohibited cases
   - Alternative methods for each prohibited case
5. **Component/Layer Boundaries**
   - Folder/layer structure rules
   - Import boundary rules
   - Props passing criteria and alternatives

### Items That Must Be Investigated in the Project Contract Packet

The following items are not fixed in the adapter but are finalized directly in each project contract packet.

- Whether the architecture style is a general layered/component structure or Feature Sliced Design (FSD)
- Whether it is a React SPA or Next.js App Router
- React Router DOM or Next.js data entry rules
- Whether TanStack Query is used and the query/mutation/invalidation strategy
- Whether React Hook Form is used and the selection criteria for `defaultValues` / `values` / `reset`
- Whether Zod or an alternative validator is used and the schema/resolver connection rules
- Suspense / fallback / error boundary strategy
- Whether accessibility (a11y), i18n, performance, and testing are required

## Primary Evidence Sources

Frontend harness rules use the following sources as primary evidence. The actual combination is narrowed in the contract packet.

- React official documentation (react.dev)
- Official documentation of the router in use (React Router, Next.js, Remix, etc.)
- Official documentation of the server state tool in use (TanStack Query, etc.)
- Official documentation of the form library in use (React Hook Form, etc.)
- Official documentation of the validator in use (Zod, etc.)
- Feature-Sliced Design official documentation (when adopted)
- MDN Web Docs

Optional supplementary tools:

- Context7 MCP
  - Can quickly augment official documentation snippet searches.
  - However, final rules and citations must be re-verified against the original official documentation.

Stack-specific seed references are defined in `stacks/<stack>.md`.

## Optional Example Pack

The frontend task adapter may reference the following example packs.

- `references/examples/frontend/README.md`
- `references/examples/frontend/ANTI_GOOD_REFERENCE.md`
- `references/examples/frontend/VALIDATION_REFERENCE.md`

Rules:

- Example packs are reference-only evidence, not normative contracts.
- The adapter itself is valid even without example packs.
- If example packs exist, verify they do not conflict with the contract packet.

## Conditional Architecture Rules: Feature Sliced Design

If the architecture style is confirmed as Feature Sliced Design (FSD) in the project contract packet, the following rules are additionally applied.

### Items That Must Be Exposed in FSD

- The range of layers used (`app`, `pages`, `widgets`, `features`, `entities`, `shared`)
- The principle that only layers actually used in the project are retained
- Layer import rule: upper layers may only import from lower layers
- `app` and `shared` are treated as exception layers without slices
- External access to a slice goes through the public API, not internal implementation
- Cross-import between different slices in the same layer is considered a code smell by default

### Items That Must Be Recorded in the Contract Packet When FSD Is Adopted

- `architecture_style: fsd`
- List of layers actually in use
- Public API policy (`index.ts` or equivalent public entry point)
- Whether cross-import exceptions are allowed
- Whether exception mechanisms like `@x` cross-reference are used
- Which upper layer is responsible for feature/widget assembly

## Anti/Good Minimum Required Pair List

The frontend harness's ANTI_PATTERNS.md **must** contain both Anti and Good pairs for each of the following cases. If only one side exists, the harness is deemed incomplete.

### State Management

| Case | Anti Content | Good Content |
|---|---|---|
| Server state duplication | Duplicating server data into local state | Subscribing directly from the server state tool |
| State tool misuse | Storing server/form/route data in global state | Using the appropriate tool for each state type |

### Data Flow

| Case | Anti Content | Good Content |
|---|---|---|
| useEffect fetch | Fetching data with useEffect | Using router data entry point or Query |
| Manual sync after mutation | Manually patching local state after mutation success | Using invalidate/revalidate |
| Route data-query duplication | Duplicate fetching the same entry data via loader and query | Separating route entry responsibility from query responsibility |

### Form/Validation

| Case | Anti Content | Good Content |
|---|---|---|
| Scattered initial value injection | Injecting initial values via repeated useEffect + setValue | Using `defaultValues`, `values`, or an explicit `reset` strategy |
| Form state duplication | Storing form values separately in local state | Using the form library as the single source of truth |
| Scattered validation | Distributing input validation across per-component conditionals | Using a single validation entry point such as schema + resolver |
| Type/runtime validation mismatch | Type definitions and runtime validation rules are out of sync | Aligning type/runtime boundaries based on the schema |

### Component Design

| Case | Anti Content | Good Content |
|---|---|---|
| Props drilling | Passing props through 2+ levels | Using alternatives such as context, store, or route data |
| Layer boundary violation | Lower layer importing from upper layer | Unidirectional dependency following layer rules |
| FSD public API bypass | Directly importing internal paths like `model/internal` from another slice | Importing only through the slice's public API |
| FSD cross-import abuse | Directly referencing another slice in the same layer, coupling the flow | Using upper layer assembly, slice merging, downward entity migration, or an agreed-upon public API strategy |

### useEffect / Suspense

| Case | Anti Content | Good Content |
|---|---|---|
| Derived value synchronization | Storing a value computable from props/state into state via effect | Render-time computation or memoization only when necessary |
| Event handling | Handling user events via effect | Using event handlers directly |
| Missing Suspense boundary | No fallback/error boundary strategy for async rendering sections | Specifying Suspense/fallback/error boundary boundaries matching the packet |

**Note**: The above list represents the minimum required pairs. Actual projects define additional pairs in the contract packet.

## Dry-Run Input/Output Examples

### Positive Case: State Management Classification Verification

**Input**: "Display user profile data on screen and provide a form for users to edit their profile."

**Expected Output (direction the harness should guide)**:

- Profile display data -> server state or route entry data
- Profile edit form -> form state
- Form initial values -> `defaultValues`/`values`/`reset` strategy matching the packet
- Save request -> mutation + invalidate/revalidate

### Negative Case: useEffect Abuse Detection

**Input**: "Fetch data from an API, store it in state, then display it on screen."

**Expected Output (pattern the harness should block)**:

- fetch inside useEffect -> detected as prohibited case
- Storing in state -> detected as server state duplication
- Alternative suggested: route entry point or TanStack Query

## Stack Branching

Additional guidance is needed depending on the technology stack within the frontend domain.

Stack detection order:

1. Check stack declarations in AGENTS.md / CLAUDE.md at the project root
2. If no declaration exists, check package.json (`next`, `react-router-dom`, `remix`, `astro`, etc.)
3. If neither declaration nor detection is possible, request the user to select a stack

Stack-specific seed reference files:

- `stacks/frontend-nextjs.md`
- `stacks/frontend-react-spa.md`

Stack files are seed references only. Actual project rules are finalized in the contract packet.

## Architecture Style Branching

Within the frontend domain, architecture style branching may be needed independently of the technology stack.

Examples:

- General layered/component structure
- Feature Sliced Design

The architecture style is specified in the contract packet separately from the stack seed. If FSD is selected, add the FSD official documentation to the primary evidence sources, and `ARCHITECTURE.md`, `ANTI_PATTERNS.md`, `VALIDATION.md` must show public API, layer rules, and cross-import prevention rules.

## Enforcement (Enforcement Rule Configuration)

When generating a frontend harness, map anti-patterns from ANTI_PATTERNS.md that can be automatically detected by ESLint to `enforcement/LINT_RULES.md`.

### Required ESLint Plugins

Include the following plugins by default depending on the stack:

- **Common**: `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-plugin-import`
- **TypeScript**: `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`
- **Next.js**: `eslint-config-next` (`next/core-web-vitals` or `next/recommended`)
- **TanStack Query**: `@tanstack/eslint-plugin-query`

### Anti-Pattern to ESLint Rule Mapping Examples

| Anti-Pattern | ESLint Rule | Severity |
|---------|------------|--------|
| useEffect fetch | Custom rule or TanStack Query plugin | error |
| Ignoring exhaustive-deps | `react-hooks/exhaustive-deps` | error |
| Import order mismatch | `import/order` | warn |
| Unused variables | `@typescript-eslint/no-unused-vars` | error |
| Excessive use of any type | `@typescript-eslint/no-explicit-any` | error (strict) / warn (moderate) |

### Severity Levels

Based on the contract packet's `enforcement_severity`:

- **strict**: Most of the above rules set to `error`. Based on `next/core-web-vitals`. Includes additional accessibility/performance rules.
- **moderate**: Only core anti-patterns set to `error`, style-related set to `warn`.
- **minimal**: Only core anti-patterns set to `warn`, the rest disabled.

## Skill Internal Reference Examples

- `references/examples/frontend/*` contains reference-only evidence extracted from legacy frontend materials in the current repository and direct examples.
- These examples are intended to demonstrate standards for document structure, Anti/Good directness, and validation strength; they are not rules to be copied verbatim into new projects.
- Examples that do not match the current project stack should only be referenced and not promoted to portable core rules.

## Design Rationale

- Coverage Contract required axes: minimum judgment axes repeatedly needed across React/router/state management/form layers
- Per-project stack/library contract: structure for reassembling official documentation into project contract packets
- FSD conditional rules: based on FSD official layer/slice/Public API/cross-import guide
- Anti/Good required pair structure: OpenAI GPT-5 Prompting Guide's XML-Tagged Instruction Blocks + Addyosmani 3-Tier Boundary System
