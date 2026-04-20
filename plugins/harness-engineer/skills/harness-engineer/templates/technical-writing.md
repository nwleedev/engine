---
domain: technical-writing
domain_type: document
language: auto
keywords: [API, documentation, guide, tutorial, reference, README, architecture, ADR, spec]
file_patterns: []
updated: 2026-04-20
---

# Technical Writing Harness

## Purpose
Define the ideal standard for technical documentation — API docs, architecture docs, READMEs, and design specs.

## Core Rules

- [ ] Every function/endpoint documented with: purpose, parameters, return value, example
- [ ] Code examples are runnable and include expected output
- [ ] Undefined acronyms and terms are explained on first use
- [ ] Active voice preferred — "The function returns X", not "X is returned by the function"
- [ ] Decision docs (ADR) include: context, considered alternatives, chosen option, rationale

## Pattern Examples

### API Endpoint Documentation

<Good>
**POST /users**
Creates a new user account.

Parameters:
- `email` (string, required): Valid email address
- `name` (string, required): Display name, 2–50 characters

Returns: `201 Created` with `{"id": "usr_123", "email": "...", "name": "..."}`

Example:
```bash
curl -X POST /users -d '{"email":"a@b.com","name":"Alice"}'
# → {"id":"usr_abc","email":"a@b.com","name":"Alice"}
```
</Good>

<Bad>
**POST /users** — Creates a user.
Parameters: email, name.
No types, no validation rules, no example, no return value.
</Bad>

## Anti-Pattern Gate

```
Function/endpoint without example?         → Add runnable code example with output
Passive voice ("is returned")?             → Convert to active ("returns")
Acronym used without definition?           → Define on first use: "ADR (Architecture Decision Record)"
ADR without considered alternatives?       → Add "Alternatives considered" section
```
