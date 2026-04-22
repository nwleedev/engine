---
description: Refresh regenerable sections of an existing domain environment (Core Framework, Working Principles, Good/Bad Example) without touching user-edited sections.
---

# /nondev-sync

Argument: $ARGUMENTS

**REQUIRED SUB-SKILL:** Use the `nondev-builder` skill to handle this command.

Invoke the nondev-builder skill now in **sync mode**. Pass `$ARGUMENTS` as the task-name argument.

- Argument must match `[a-z0-9-]+` (an existing domain slug; e.g. `market-research`)
- If no argument is provided, stop and reply: "Usage: `/nondev-sync <task-name>` — provide an existing domain name."
- The skill will verify the domain exists, then regenerate `## Core Framework`,
  `## Working Principles`, and `## Good Example / Bad Example` via fresh web search,
  while preserving `## Source Collection Strategy` and `## Custom Examples`.
