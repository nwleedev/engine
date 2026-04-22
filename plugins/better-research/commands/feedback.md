---
description: Record a bias pattern observed in Claude's response for session correction and future learning
---

Argument: $ARGUMENTS

The user has identified a bias pattern or wrong decision in Claude's recent response and is quoting the exact text as evidence.

Steps:

1. Read the quoted text from $ARGUMENTS.
   If $ARGUMENTS is empty, ask: "Which response, and which part of it, would you like to record?"
2. Append a new entry to `.claude/feedback/raw.md`:
   - Create `.claude/feedback/` directory and file if they do not exist
   - If creating a new file, write header: `<!-- checkpoint: <current UTC ISO8601> -->`
   - Append the entry block:
     ```
     ---
     ts: <current UTC ISO8601>
     text: "<$ARGUMENTS>"
     ---
     ```
3. In one sentence, name the bias pattern present in the quoted text (e.g., "convenience-driven method selection", "task avoidance due to quantity").
4. State concretely how you will approach this differently for the rest of this session.
