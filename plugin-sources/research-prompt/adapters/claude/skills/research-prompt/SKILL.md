---
name: research-prompt
description: Generate a ChatGPT Deep Research Markdown prompt from live project context without calling external APIs.
---

# Research Prompt

Create one Deep Research prompt artifact from the current project.

## Run

Use the plugin command or helper script with `--harness claude`.

## Output

The helper writes exactly one Markdown prompt under:

```text
.claude/deep-research-prompts/
```

Do not create metadata, cache, index, latest, or database files. Do not include secrets. If a requested path is denied, record the denial reason in the prompt instead of reading the file.
