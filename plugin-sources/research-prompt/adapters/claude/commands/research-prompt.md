Generate a Deep Research prompt artifact for the current project.

Run the research-prompt helper from the project root:

```bash
python3 plugins/claude/research-prompt/scripts/research_prompt.py --harness claude --problem "<research question>" --path <relative-path>
```

Pass the user's research question as `--problem`, and include explicitly mentioned project paths with repeated `--path` arguments. The helper fills `--project-root` from the current working directory and the output date from today's date when they are not supplied.
