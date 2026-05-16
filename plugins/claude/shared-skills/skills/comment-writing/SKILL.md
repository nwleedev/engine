---
name: comment-writing
description: Use when writing, reviewing, or updating comments and documentation comments across any language or technology stack.
metadata:
  short-description: Write stack-appropriate comments that help new teammates understand code quickly.
---
<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/shared-skills/skills/comment-writing/SKILL.md -->


# Comment Writing

## Purpose

Use this skill to write, review, or update comments, doc comments, API documentation, schema documentation, and configuration or infrastructure documentation in the format expected by the detected language and project.

The goal is not many comments. The goal is accurate, minimal, stack-appropriate comments that help a new teammate understand purpose, constraints, side effects, failure modes, invariants, operational hazards, and public API behavior that names, types, tests, and structure do not already make clear.

Prefer the project's existing convention over a generic style. When the project convention conflicts with official tooling behavior, record the conflict and ask for clarification or use a `docs-researcher handoff`.

## When to use

- When adding or updating doc comments for public/exported APIs.
- When explaining complex logic that a new teammate cannot understand from names, types, tests, and structure alone.
- When cleaning up stale comments that conflict with code.
- When improving API, schema, configuration, or infrastructure manifest documentation.
- When the user asks for comments, documentation, doc comments, API docs, or explanations for a new teammate.

## Inputs to inspect

- Target language, file extension, framework, schema format, and documentation generator.
- Public/exported symbols, schema fields, configuration keys, infrastructure manifests, and generated-code boundaries.
- Existing comment style near the changed files.
- README, API docs, design docs, migration notes, and public API policy.
- Lint and documentation tooling such as TypeDoc, TSDoc, Javadoc, Dokka, rustdoc, godoc, pydoc, Doxygen, phpDocumentor, YARD, DocC, OpenAPI, GraphQL, or Proto tooling.
- Naming conventions, type shapes, tests, and examples that already explain behavior.
- Security, privacy, performance, compatibility, concurrency, async, thread-safety, and operational constraints.
- Existing debt marker convention for `TODO`, `FIXME`, `HACK`, and `NOTE`.

## Workflow

1. Detect the target language, stack, file extension, schema format, and documentation tooling.
2. Inspect nearby comments, project documentation, lint rules, doc generation config, and public API convention.
3. Identify public/exported surfaces and internal logic that require comment or documentation coverage.
4. Identify what a new teammate must know: purpose, domain concepts, constraints, invariants, side effects, errors, failure modes, security or privacy limits, compatibility behavior, async behavior, and operational hazards.
5. Before explaining unclear code with comments, consider whether clearer code before comments is possible within the approved scope: better names, named constants, extracted expressions/functions, enums, typed options, classes, structs, or smaller units.
6. If clearer code would require unrelated refactoring, do not perform it silently. Report the improvement as a follow-up or ask for approval.
7. Select the project-preferred comment format. If no project convention exists, use the stack-specific format from `../../references/comment-specs-by-stack.md`.
8. Write minimal but sufficient comments only where they add information the code does not already say.
9. Do not repeat names, types, tests, or obvious implementation mechanics.
10. Delete or update stale comments that conflict with code.
11. Validate with available doc, lint, build, type, schema, or test commands.
12. Use a `docs-researcher handoff` only when official comment format or documentation tooling behavior needs verification.
13. Use a `code-reviewer handoff` when independent review is needed for comment quality, stale comments, readability, or unclear code hidden by comments.
14. Report detected stack, selected convention, changed or proposed comments, validation evidence, and remaining ambiguity.

## Documentation target decision matrix

| Target | Comment format | Must explain | Avoid | Validation |
| --- | --- | --- | --- | --- |
| public/exported function | Stack doc comment. | Purpose, inputs, outputs, errors, side effects, constraints, async behavior when relevant. | Restating parameter names or static types. | Doc generator, lint, type check, tests. |
| public/exported class or type | Stack doc comment. | Role, lifecycle, invariants, usage constraints, thread-safety or mutability when relevant. | Implementation internals unrelated to use. | Doc generator, API docs, examples. |
| module/package | Package, module, or file-level doc format. | Scope, key entry points, what belongs here, usage expectations. | Repeating every symbol. | Doc generator or package docs. |
| complex internal algorithm | Ordinary implementation comment near the code. | Why this algorithm, invariants, tradeoffs, failure modes. | Line-by-line mechanics. | Tests, benchmarks, reviewer check. |
| non-obvious business rule | Ordinary implementation comment or domain doc near rule. | Domain reason, source of rule, exception conditions, removal condition. | Guessing policy intent. | Tests, issue/design link when available. |
| concurrency/async behavior | API doc and implementation comment where needed. | Ordering, cancellation, retries, locking, thread-safety, races, idempotency. | Vague "async-safe" claims. | Tests, race tools, docs review. |
| error handling and failure mode | API doc, implementation comment, schema description. | Error types, safe failure, retryability, caller responsibility. | Listing impossible errors. | Tests and API docs. |
| security/privacy-sensitive code | Comment close to policy or boundary. | Constraints, redaction, auth assumptions, data handling limits. | Secrets, credentials, internal endpoints, private data. | Security review and tests. |
| configuration file | Native description, adjacent comment, or README. | Units, default, allowed values, operational impact, rollback risk. | Comments that drift from actual defaults. | Config validation, schema validation. |
| database schema/migration | `COMMENT ON`, migration note, or schema docs. | Data meaning, compatibility, backfill, rollback, lock or downtime risk. | Repeating column names. | Migration tests, schema diff, database validation. |
| infrastructure manifest | Native fields, annotations, labels, adjacent comment. | Ownership, rollout, permissions, networking, operational hazard. | Comments that duplicate YAML keys. | IaC validation, dry run, policy checks. |
| generated code boundary | Generator source docs or boundary docs. | What is generated, source of truth, manual edit prohibition. | Hand-editing generated output. | Regeneration and diff check. |

## Stack-specific comment formats

Use this section only for routing. Keep row-level rules and official source details in `../../references/comment-specs-by-stack.md`.

1. Project convention wins first when it is explicit and compatible with the stack tooling.
2. If no convention exists, use `../../references/comment-specs-by-stack.md` as the source-backed format reference.
3. Keep the selected format minimal and consistent with the documentation target, then validate with the project's doc, lint, build, schema, or test command when available.

Covered formats include Javadoc, KDoc, JSDoc/TSDoc, docstring/PEP 257, Go doc comments, rustdoc, XML documentation comments, PHPDoc, RDoc/YARD, Swift documentation comments, Objective-C documentation comments, Doxygen, COMMENT ON/schema comments, Shell usage comments, Terraform descriptions, Dockerfile labels/comments, Kubernetes annotations/labels/operation notes, and OpenAPI/GraphQL/Proto descriptions/comments.

## Comment quality rules

- Do not repeat what the code already says.
- Explain why, not just what.
- Public/exported API comments must describe purpose, inputs, outputs, errors, side effects, and constraints when relevant.
- Internal comments should explain non-obvious decisions, invariants, tradeoffs, failure modes, and operational hazards.
- Comments must stay close to the code, schema, or configuration they explain.
- Prefer better names, types, tests, and small functions over comments when they solve the comprehension problem inside the approved scope.
- Avoid speculation. Mark uncertainty explicitly only when unavoidable.
- Avoid misleading comments that can become stale after small implementation changes.
- Debt markers must include owner, reason, removal condition, or tracking reference when project convention allows.
- Security/privacy-sensitive comments must not reveal secrets, credentials, internal endpoints, private data, or sensitive operational details.
- Generated code should usually not be hand-commented unless the generator source or boundary requires documentation.

## Review handoff

Use this `docs-researcher handoff` only when official format or tooling behavior needs verification:

```text
docs-researcher handoff
- target language or stack:
- target files and symbols:
- detected project comment convention:
- exact documentation question:
- candidate official sources already checked:
- version or tool context:
- unresolved ambiguity:
```

Use this `code-reviewer handoff` when comment quality or readability review is needed:

```text
code-reviewer handoff
- changed files and symbols:
- public/exported APIs affected:
- selected comment format and rationale:
- comments added, updated, or removed:
- stale comments removed or still suspected:
- why-oriented explanations added:
- unclear code made clearer before comments:
- validation commands run:
- known documentation gaps:
- areas intentionally left undocumented:
```

## Development work

- Read nearby code, tests, comments, public APIs, schema files, and docs before adding or changing comments.
- Prefer clearer code before comments when the approved scope allows a small readability change.
- Keep comment work close to the behavior, API, schema, or operational boundary it explains.
- Validate with the narrowest available doc, lint, build, type, schema, or test command.
- Prepare a `docs-researcher handoff` or `code-reviewer handoff` only when the task needs that independent check.

## Non-development work

- Use this skill for documentation-only reviews, comment standards, style guides, API documentation guidance, and comment quality checklists.
- Prefer official or project-specific documentation conventions and reference `../../references/comment-specs-by-stack.md` for source-backed details.
- Separate verified stack rules from local editorial preferences.
- Record unresolved convention conflicts instead of inventing a new style.
- Route broad requirement ambiguity to `requirements-packet` and source-backed research to `research-plan`, `source-ledger`, or `claim-evidence-map`.

## Output

- detected stack
- detected comment convention
- files and symbols requiring comments
- comment changes made or proposed
- stale comments removed or updated
- validation commands run
- docs-researcher handoff, if official spec verification is needed
- code-reviewer handoff, if comment quality review is needed
- remaining ambiguous or undocumented areas
- risks if comments cannot be validated automatically

## Do not

- Do not add large volumes of low-value comments.
- Do not repeat obvious code, names, types, or tests.
- Do not ignore project comment style to force a generic convention.
- Do not assert unverified intent or design background.
- Do not put secrets, credentials, internal endpoints, private data, or sensitive operational details in comments.
- Do not hand-comment generated code unless the generator source or boundary requires documentation.
- Do not add debt markers without owner, reason, removal condition, or tracking reference when project convention allows.
- Do not omit a handoff when official format verification or comment quality review is needed.
- Do not turn comment work into unrelated refactoring without approval.
