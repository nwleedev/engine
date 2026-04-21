# better-research

Enforces structured, bias-resistant research and implementation in Claude Code. Registers three hooks to combat frame bias at session start, during prompts, and at the implementation boundary.

## How it works

better-research registers three hooks:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Once at session start | Injects 4-step anti-frame-bias block unconditionally |
| `UserPromptSubmit` | Before Claude processes your message | Injects 6-step A+C criterion-guided evaluation block unconditionally; additionally injects research protocol when `/q` marker is present |
| `PreToolUse` | Before every Edit or Write tool call | Calls `claude-haiku-4-5-20251001` to evaluate whether the change is structural or superficial; blocks if verdict is superficial with high confidence |

### SessionStart — Session-level anti-frame-bias

Injected once at session start. Primes Claude to suspend framing, enumerate alternatives, and verify assumptions.

### UserPromptSubmit — Criterion-guided evaluation

Injected on every prompt unconditionally. The 6-step `<cognitive-debiasing>` block adds two steps beyond the session-level block:

- **Step 5 — EVALUATE:** Select from enumerated options using only Correctness, Standard compliance, or Maintainability. PROHIBITED criteria: fewer changes required / faster to implement / more familiar.
- **Step 6 — DECLARE:** Commit to a root cause, structural fix, and confirm no prohibited criteria influenced the selection — before writing any code.

When a `/q`, `/query`, or `/research` marker is present, the research protocol (SKILL.md) is additionally injected on top of the A+C block — the two are additive, not mutually exclusive.

### PreToolUse — Superficial implementation blocker

Intercepts every `Edit` and `Write` tool call. Sends the diff to `claude-haiku-4-5-20251001` via `claude -p` and blocks the call if the verdict is `superficial` with `high` confidence. Ambiguous changes (medium/low confidence, or `unclear` verdict) pass through.

Blocked if the change is one of:
- Silencing exceptions without fixing the cause
- Adding bypass flags or conditional routing around broken logic
- Only renaming/reformatting with no behavioral change
- Adding an abstraction layer over broken code
- Hardcoding values that belong in configuration or logic
- Adding special-case branches to work around general logic failures
- Catching exceptions to hide errors instead of fixing them

## Installation

```
/plugin marketplace add nwleedev/better-research
```

Or install the full engine marketplace:

```
/plugin marketplace add nwleedev/engine
```

## Usage

Prefix any question with `/q`, `/query`, or `/research` to activate the research protocol:

```
/q what is the difference between concurrency and parallelism?
/research why does my Dockerfile cache break on every build?
/query should I use Redis or Memcached for session storage?
```

Without the marker, Claude still applies the 6-step A+C evaluation block. With the marker, the research protocol runs on top of it.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `RESEARCH_PERSPECTIVES` | _(empty)_ | Comma-separated list of viewpoints injected into every research request |

When `RESEARCH_PERSPECTIVES` is set, Claude considers each listed perspective even without a `/q` marker.

Example `.env`:

```
RESEARCH_PERSPECTIVES=security,performance,maintainability
```
