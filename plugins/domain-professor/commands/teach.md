---
description: Generate learning materials for a domain or concept
---

Refer to the `domain-professor` skill and handle the following request: $ARGUMENTS

Processing order:
1. Check `.claude/textbooks/` in the project root
2. Create files for the requested domain/concept, or review existing coverage
3. Inform the user of the generated file paths and suggest the next learning step

If no domain is specified, ask the user which domain they want to learn.
