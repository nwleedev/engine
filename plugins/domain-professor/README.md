# domain-professor

Generates structured learning materials for any domain. Run `/teach` to create a textbook, or let the plugin auto-detect unfamiliar domains from your session history and prompt you to learn them.

## How it works

domain-professor runs two hooks and registers two commands:

| Hook | When it fires | What it does |
|---|---|---|
| `SessionStart` | Every session open | Scans recent session summaries for unfamiliar domain terms and reports them |
| `Stop` | Every session end | Detects domains encountered during the session |

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

### /teach

```
/teach <domain>
/teach <domain> <concept>
```

Examples:

```
/teach kubernetes
/teach kubernetes pod scheduling
/teach react server components
```

- If the textbook does not exist: creates `01-overview/what-is-<domain>.md` and `INDEX.md`.
- If the textbook exists but no concept is given: reviews existing coverage and suggests the next stage.
- If a concept is given: creates the concept file at the appropriate stage. If it already exists, suggests `/teach-more`.

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
| `DOMAIN_PROFESSOR_DOMAINS` | _(empty)_ | Comma-separated list of domains to auto-detect. When empty, all encountered domains are candidates |

Example `.env`:

```
DOMAIN_PROFESSOR_LANGUAGE=Korean
DOMAIN_PROFESSOR_DOMAINS=kubernetes,react,fastapi
```
