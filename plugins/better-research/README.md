# better-research

Enforces a structured research protocol in Claude Code. When you prefix a prompt with `/q`, `/query`, or `/research`, Claude executes a 5-step process before answering: hypothesis, source validation, counter-argument check, root cause analysis, then a final answer.

## How it works

better-research registers one hook:

| Hook | When it fires | What it does |
|---|---|---|
| `UserPromptSubmit` | Before Claude processes your message | Detects research markers; injects the protocol and any configured perspectives |

**Trigger markers:** `/q`, `/query`, `/research` — case-insensitive, anywhere in the prompt.

```
/q why does React re-render when state hasn't changed?
/research what causes connection pool exhaustion in PostgreSQL?
/query difference between optimistic and pessimistic locking
```

The marker is stripped before Claude sees the question. Claude then executes:

1. **Initial Hypothesis** — draft answer, not a conclusion
2. **Source Validation** — 2+ independent sources (official docs, specs, or source code preferred); any claim with fewer than 2 sources is marked `[UNVERIFIED]`
3. **Counter-Argument Check** — at least one limitation or condition where the answer does not hold
4. **Root Cause Analysis** — recursive "why" chain (minimum 3 levels); no solution is proposed until the root cause is identified
5. **Final Answer** — conclusion → evidence → limitations → sources

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

Without the marker, Claude answers normally. With the marker, Claude works through all 5 steps before giving a final answer.

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
