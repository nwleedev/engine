# Common Bootstrap Phase

## Purpose

This document defines the common bootstrap phase that `harness-engine` executes when coverage gaps remain after the common research phase or when an unknown domain is encountered.

This phase is separate from task adapters. Its role is one of the following two:

The path for creating engine assets alongside when no adapter exists for a representative category is handled in `harness-engine`'s `engine-asset bootstrap` execution path, not in this document.

- **New mode**: Creates a draft contract for a new domain that cannot be described by the representative category set.
- **Supplement mode**: Keeps the existing task adapter but supplements only the domain knowledge lacking for the current project.

## When to Use

### New Mode

- Cannot be described by the representative category set (`frontend`, `research`, `backend`, `testing`, `security`, `ops`).
- No task adapter exists for the domain.
- The user explicitly stated that a new domain harness is needed.

### Supplement Mode

- A task adapter exists but gaps are detected in the coverage gap check.
- The task adapter's methodology is sufficient, but specific knowledge for the current project is lacking.
- Examples: `frontend` + unfamiliar framework, `research` + unfamiliar industry/topic

## Required Principles

- Include human-in-the-loop verification.
- Bootstrap results are fundamentally drafts or supplementary information.
- Project-specific examples and failure cases are fundamentally `local evidence pack` candidates.
- In supplement mode, do not replace the existing task adapter's methodology (HOW).
- Bootstrap results are first organized into a project contract packet, then reflected in harness deliverables.

## Procedure

1. Role Definition
   - Define Role, Goal, and Backstory concretely.
2. Draft Coverage Contract
   - At least 4 core axes
   - At least 3 failure modes
   - Primary evidence sources
   - Quality criteria
3. User Verification
   - Confirm missing axes, unnecessary axes, real failure cases, and additional sources.
4. Specify Conservative Defaults
   - Fill items the user could not answer with conservative defaults and mark them.
5. Pass to Generation Stage
   - Record confirmed coverage, failure modes, evidence sources, and quality criteria in the contract packet first.
   - In new mode, close the scope to include the formal task adapter and, if needed, example pack/seed assets.

## Output to Pass to Generation Stage

- bootstrap mode: `new` or `supplement`
- Role / Goal / Backstory
- Confirmed Coverage Contract
- User verification results
- Conservative default markers
- Fields to reflect in the contract packet
- In new mode, the adapter path to create and, if needed, example/seed asset paths

## Failure Signals

- Entering an unknown domain and writing an adapter or harness directly without bootstrap.
- In supplement mode, overwriting the existing adapter's methodology itself.
- Leaving only generic titles and generic quality criteria without user verification.
- Writing local evidence obtained through bootstrap as if it were portable core rules.
