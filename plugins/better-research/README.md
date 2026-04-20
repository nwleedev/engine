# better-research

Enforces structured, bias-resistant research in Claude Code. Registers two hooks to combat frame bias at session start and during prompts.

## How it works

better-research registers two hooks:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Once at session start | Injects anti-frame-bias XML block unconditionally (Layer 1a) |
| `UserPromptSubmit` | Before Claude processes your message | Two paths: keyword-triggered debiasing (Layer 1b) and marker-triggered research protocol (Layer 2) |

### Layer 1a — Session-level anti-frame-bias

Injected once at session start, regardless of the prompt. Primes Claude to suspend framing, enumerate alternatives, and verify assumptions before every response.

### Layer 1b — Keyword-triggered cognitive debiasing

When the prompt contains design or brainstorming keywords, the `<cognitive-debiasing>` block is injected automatically:

- **Korean:** 설계, 방법, 접근법, 구현, 어떻게, 전략
- **English:** design, approach, architect, implement, strategy

No marker required — detection is automatic.

### Layer 2 — Marker-triggered research protocol

**Trigger markers:** `/q`, `/query`, `/research` — case-insensitive, anywhere in the prompt.

```
/q why does React re-render when state hasn't changed?
/research what causes connection pool exhaustion in PostgreSQL?
/query difference between optimistic and pessimistic locking
```

The marker is stripped before Claude sees the question. Claude then executes a 6-step protocol:

- **Step 0 — Expansive Framing** — restate the question broadly; list 3+ alternative interpretations
- **Step 1 — Initial Hypothesis** — draft answer, not a conclusion
- **Step 2 — Source Validation** — 2+ independent sources (official docs, specs, or source code preferred); any claim with fewer than 2 sources is marked `[UNVERIFIED]`
- **Step 3 — Counter-Argument Check** — at least one limitation or condition where the answer does not hold
- **Step 4 — Root Cause Analysis** — recursive "why" chain (minimum 3 levels); no solution is proposed until the root cause is identified
- **Step 5 — Final Answer** — conclusion → evidence → limitations → sources

## Installation

```
/plugin marketplace add nwleedev/better-research
```

Or install the full engine marketplace:

```
/plugin marketplace add nwleedev/engine
```

## Usage

Prefix any question with `/q`, `/query`, or `/research`:

```
/q what is the difference between concurrency and parallelism?
/research why does my Dockerfile cache break on every build?
/query should I use Redis or Memcached for session storage?
```

Without the marker, Claude answers normally (though Layer 1a and Layer 1b still apply). With the marker, Claude works through all 6 steps before giving a final answer.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `RESEARCH_PERSPECTIVES` | _(empty)_ | Comma-separated list of viewpoints injected into every research request |

When `RESEARCH_PERSPECTIVES` is set, Claude considers each listed perspective even without a `/q` marker. Use this to enforce multi-angle analysis on all responses.

Example `.env`:

```
RESEARCH_PERSPECTIVES=security,performance,maintainability
```

With this set, every Claude response considers security, performance, and maintainability implications.
