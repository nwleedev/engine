---
name: research-prompt
description: Generate a ChatGPT Deep Research Markdown prompt from live project context without calling external APIs.
---

# Research Prompt

Create one Deep Research prompt artifact from the current project.

## Run

Use the helper script next to this skill:

```bash
python3 /path/to/skills/research-prompt/scripts/research_prompt.py --harness codex --problem "<research question>" --path <relative-path>
```

## Output

The helper writes exactly one Markdown prompt under:

```text
.codex/deep-research-prompts/
```

Do not create metadata, cache, index, latest, or database files. Do not include secrets. If a requested path is denied, record the denial reason in the prompt instead of reading the file.
