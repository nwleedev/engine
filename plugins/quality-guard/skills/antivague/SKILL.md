---
name: antivague
description: Re-examine the last response for text abbreviation patterns and rewrite more thoroughly, then record the pattern
---

Argument: $ARGUMENTS

The user suspects the last response was too vague, incomplete, or fragmented.

Steps:

1. Determine the scope to re-examine:
   - If $ARGUMENTS is non-empty: treat $ARGUMENTS as the specific passage to examine.
   - If $ARGUMENTS is empty: examine the entire previous response.

2. Identify text abbreviation patterns in the target scope. Look for:
   - Vague enumeration: phrases like "there are several ways", "various options exist" with no specifics
   - Unsupported claims: principles stated without concrete code examples, numbers, or real cases
   - Skipped steps: procedural explanations that omit intermediate steps
   - Decontextualised conclusions: final statements given without the reasoning that leads to them

3. Explicitly name each pattern found and the specific passage where it appears.

4. Rewrite the identified passages with:
   - Concrete examples or code snippets replacing vague descriptions
   - Step-by-step breakdowns where steps were skipped
   - Actual numbers, names, or references where abstract terms were used
   - Full reasoning chains where conclusions were stated without context

5. For each pattern found, append one entry to `.claude/feedback/raw.md`:
   - Create `.claude/feedback/` directory and file if they do not exist.
   - If creating a new file, write header: `<!-- checkpoint: 1970-01-01T00:00:00Z -->`
   - For each pattern, append an entry block in exactly this format (ts then text, no other fields):
     ```
     ---
     ts: <current UTC ISO8601, e.g. 2026-04-24T10:00:00Z>
     text: "[text-abbreviation] <one sentence describing this specific pattern>"
     ---
     ```

6. Confirm in one sentence that the pattern has been recorded.
