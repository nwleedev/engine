Generate one stack-agnostic ChatGPT Deep Research Markdown prompt from live project context. Use user-provided paths, logs, symbols, and visible project signals instead of assuming one language or runtime.

Run the deep-research-prompt-export helper from the project root:

```bash
python3 plugins/claude/deep-research-prompt-export/scripts/research_prompt.py --harness claude --problem "<research question>" --path <relative-path>
```

Pass the user's research question as `--problem`, and include explicitly mentioned project paths with repeated `--path` arguments. The helper fills `--project-root` from the current working directory and the output date from today's date when they are not supplied.
It writes exactly one prompt under `.claude/deep-research-prompts/`.
