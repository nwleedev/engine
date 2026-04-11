# Operator Stack Adapter

## Purpose

When harness-engine generates or augments a harness for designing the agent operating environment and harness deployment structure, this adapter is additionally applied after the common `research` phase to enforce the minimum contract for the `operator-stack` task_type.

## Coverage Contract

An operator stack harness must include the following items.

### Required Axes

1. **Operating Layer Model**
   - Machine, user, repository, session, team, and deployment layers
2. **Persistent Configuration Model**
   - Personal defaults, project overrides, and one-off flag boundaries
3. **Work Loop**
   - Research, implementation, verification, review, and resume procedures
4. **Permission/Control Model**
   - Approval policies, sandbox, MCP, skills, hooks, logging
5. **Deployment Structure**
   - Comparison of the current copy-based model vs. the long-term package-based model
6. **Retention Decisions**
   - Which assets to retain and which to change

### Items That Must Be Finalized in the Contract Packet

- Target operating surface (Claude Code, Codex, etc.)
- List of retained assets in the current repository
- Packaging scope
- Override preservation policy
- Criteria for separating follow-up implementations

## Primary Evidence Sources

1. Tool official documentation
2. Harness structure and scripts in the current repository
3. Official best practices or config references
4. Results from existing session investigations

Rules:

- Do not design an operator stack based solely on assumptions about internal-only features.
- First finalize the operating layers that can be explained through the public surface.

## Anti/Good Minimum Required Pairs

### Operating Goals

| Case | Anti | Good |
|---|---|---|
| Chasing internal privileges | Documenting with the goal of replicating employee-only features | Designing the best possible operating system achievable by external users |
| Mixing deployment and rules | Connecting deployment mechanism issues to discarding core harnesses | Judging rule layer retention and deployment mechanisms separately |

### Layer Design

| Case | Anti | Good |
|---|---|---|
| Configuration mixing | Not distinguishing between user defaults and project rules | Separating user/repo/session layers |
| Session neglect | Placing session structure outside the operator stack for long-running work | Including sessions and evidence as part of the operating layers |

### Deployment

| Case | Anti | Good |
|---|---|---|
| Immediate rewrite | Implementing a new CLI immediately without evaluating current assets | Writing RFC, package architecture, and migration plan first |
| Override destruction | Overwriting project-local assets during the packaging process | Maintaining portable core / adapter / evidence boundaries |

## Dry-Run Input/Output Examples

### Positive Case

**Input**: "I want to design an npx-based deployment structure instead of the current sync script."

**Expected Output**:

- Inventory of core assets to retain
- Deployment method comparison table
- Package architecture draft
- Phased migration plan

### Negative Case

**Input**: "The goal is to replicate everything that looks like an internal feature as-is."

**Expected Output**:

- Redefine operator-stack objectives
- Adjust scope to a public surface-based operating model

## Design Rationale

- Both Claude Code and Codex expose persistent configuration, repository directives, tool connections, and review/verification loops as official operating surfaces.
- Therefore, improving operating quality for external users is better approached through designing a layered work environment rather than speculating about internal features.
