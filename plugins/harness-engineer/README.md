# harness-engineer

Injects domain-specific coding standards into every Claude Code work turn and detects violations at session end. Define your ideal patterns once; Claude enforces them automatically.

## How it works

harness-engineer runs four hooks and registers three commands:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Every session open | Loads all harness files from `.claude/harness/` as context |
| `UserPromptSubmit` | Before each user message | Reminds Claude to check harness patterns before acting |
| `PreToolUse` | Before each tool call | Enforces harness compliance before writing or editing files |
| `Stop` | Every session end | Scans work done this session; writes violations to `.claude/harness/violations.log` |

Harness files are stored in `.claude/harness/`:

```
.claude/harness/
├── <domain>.md        # Coding standards for a tech stack or domain
└── violations.log     # Appended each session; used by /update-harness
```

Each harness file contains: file patterns, keywords, core rules (checklist), `<Good>`/`<Bad>` code examples, and an anti-pattern gate (self-check questions).

## Installation

```
/plugin marketplace add nwleedev/harness-engineer
```

Or install the full engine marketplace:

```
/plugin marketplace add nwleedev/engine
```

## Usage

### /create-harness

```
/create-harness <tech stack description>
```

Examples:

```
/create-harness Next.js 14 App Router + TanStack Query + Tailwind CSS
/create-harness FastAPI + SQLAlchemy + PostgreSQL
/create-harness React Native + Expo + Zustand
```

The plugin fetches official documentation, extracts best practices, and writes a harness file to `.claude/harness/<domain>.md`. After creation, it shows the `file_patterns` list — adjust if your project structure differs.

### /update-harness

```
/update-harness
/update-harness <domain>
```

Reads `violations.log` for repeated violations (3+ occurrences) and proposes adding them to the harness `## Anti-Pattern Gate`. Also fills in rules that lack `<Good>`/`<Bad>` examples. Confirms each change before writing.

### /evaluate-harness

```
/evaluate-harness
/evaluate-harness <domain>
```

Scores the harness on 5 criteria (each out of 10):

| Criterion | Full score condition |
|---|---|
| Pattern example concreteness | All rules have `<Good>`/`<Bad>` code examples |
| Anti-pattern coverage | All `violations.log` entries appear in the gate |
| File length | Under 500 lines |
| Violations reflected | No repeated violations missing from gate |
| Recency | Updated within 30 days |

## Configuration

| Variable | Default | Description |
|---|---|---|
| `HARNESS_LANGUAGE` | `auto` | Language for generated harness content. `auto` follows the current conversation language; `ko` or `en` force a specific language |

Example `.env`:

```
HARNESS_LANGUAGE=en
```
