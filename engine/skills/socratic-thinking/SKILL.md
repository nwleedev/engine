---
name: socratic-thinking
description: "Socratic thinking principles. A cognitive framework applying explore-first, single-question discipline, assumption probing, closed scope, and inline verify-evaluate-repair loops. Referenced by plan-readiness-checker; also user-invocable."
user-invocable: true
---

# Socratic Thinking Principles

Cognitive principles applying Socratic thinking to AI work workflows. "Recognize what you don't know, explore, and ask only the single most important question."

Source: [socrates-protocol](https://github.com/jiyeongjun/socrates-protocol) core principles adapted to harness architecture.

---

## 1. Explore Before Asking

Before asking the user, first search for answers in existing artifacts.

Procedure:
1. Explore related code, config, and tests via Glob/Grep/Read
2. Understand context from change history and commit messages via git log
3. Check for clues in existing plans, session records, and harness skills
4. If exploration resolves the issue, proceed without asking. Ask only when resolution is impossible

Key: **Artifact recovery always takes priority over asking the user.**

---

## 2. One Load-Bearing Question

When a question is needed, ask **only one** question that most significantly changes the implementation direction, then stop.

Rules:
- Maximum 1 question per turn
- Present 2-3 specific options with trade-offs for each
- After asking, do not proceed with assumptions — **stop immediately** and wait for the answer
- If there are additional questions, list them as "follow-up questions" but proceed only after the current question is answered

Anti-pattern: Dumping 3-5 questions as a numbered list all at once.

---

## 3. Assumption Probing

Before finalizing an implementation approach, ask yourself: **"Under what conditions would this approach be wrong?"**

Procedure:
1. List the assumptions of the current approach
2. Identify the most dangerous assumption (one that would overturn the entire approach if wrong)
3. Verify the most dangerous assumption first (read code, run tests, or check constraints)
4. Explicitly record unverifiable assumptions in the plan

Key: Focus on **falsifiability**, not certainty.

---

## 4. Closed Scope Default

Implement only what was requested. Do not add unrequested features.

Rules:
- Detect scope expansion signals: "while we're at it", "for completeness", "might as well"
- When these signals are detected, separate from the current task and suggest separately
- Even if related improvements are discovered, complete the current task first then suggest separately
- Scope expansion requires **explicit user approval**

Anti-pattern: Refactoring surrounding code or adding types while fixing a bug.

---

## 5. Inline Verify-Evaluate-Repair Loop

After implementation, complete the verify-evaluate-repair cycle within the current turn.

Loop:
1. **Verify**: Run the narrowest check (type check, single test, lint, etc.)
2. **Evaluate**: Does the result meet the plan's success criteria?
3. **Repair**: On failure, identify the cause and attempt 1 repair
4. **Re-verify**: Re-run the same check after repair

Limit: **Maximum 1 repair**. If re-repair is needed, report the failure and stop.

Key: Do not rely solely on post-review (work-reviewer) for verification — perform it **during implementation**.

---

## 6. Protected Surface Awareness

Changes touching the following surfaces require extra care in the plan:

- Public API signatures
- Database schema / migrations
- Authentication / authorization
- Billing / payment
- Deployment configuration

When changing these surfaces:
- Specify **what is being changed** in the plan
- Include a **rollback strategy**
- Do not choose silent migration strategies

No separate agent needed. The plan-readiness-checker verifies these items during readiness checks.

---

## Application Timing

| Principle | Primary Application Stage |
|-----------|--------------------------|
| Explore Before Asking | Planning stage (before questions) |
| One Load-Bearing Question | Planning stage (ambiguity resolution) |
| Assumption Probing | Planning stage (before finalizing approach) |
| Closed Scope | All stages |
| Inline Verify-Evaluate-Repair | Implementation stage |
| Protected Surface Awareness | Planning stage (when writing plans) |
