# domain-professor

Generates structured learning materials for any domain. Run `/teach` to create a textbook, or let the plugin auto-detect unfamiliar domains from your session history and prompt you to learn them.

## How it works

domain-professor runs three hooks and registers three commands:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Every session open | Clears the professor flag and injects the textbook table of contents |
| `UserPromptSubmit` | Every user prompt (when active) | Injects professor SKILL.md into context to keep learning mode alive |
| `Stop` | Every session end | Detects domains from the transcript and generates textbook files |

Textbooks are created under `.claude/textbooks/<domain>/`:

```
.claude/textbooks/<domain>/
├── INDEX.md
├── 01-overview/
│   └── what-is-<domain>.md
├── 02-core-concepts/
│   └── <concept>.md
└── 03-advanced/
    └── <concept>.md
```

Each file follows the Feynman technique: plain-language summary, key concepts, real-world examples, and prerequisite links.

## Installation

```
/plugin marketplace add nwleedev/domain-professor
```

Or install the full engine marketplace:

```
/plugin marketplace add nwleedev/engine
```

## Usage

### /toggle

Activates or deactivates professor mode for the current session.

```
/domain-professor:toggle
```

- When **active**: every prompt injects the professor role so Claude continuously teaches while you work.
- When **inactive**: professor mode is off; the Stop hook still runs but skips textbook generation.

### /teach

Executes a free-form task in professor mode and generates textbook files for all domains encountered.

```
/teach <any task description>
```

Examples:

```
/teach explain how kubernetes pod scheduling works
/teach help me write a React hook for debounced input
/teach what is options pricing in finance?
```

Identifies the domain(s), executes the task, and creates or updates files under `.claude/textbooks/<domain>/`.

### /teach-more

```
/teach-more <path>
```

Drills deeper into an existing concept file:

```
/teach-more .claude/textbooks/kubernetes/01-overview/what-is-kubernetes.md
```

Creates a subfolder with 3–5 detail concept files and appends a "Further Reading" section to the original. Updates `INDEX.md`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DOMAIN_PROFESSOR_LANGUAGE` | `English` | Language for generated textbook content |

Example `.env`:

```
DOMAIN_PROFESSOR_LANGUAGE=Korean
```
