# harness-builder

Dynamically sets up quality harnesses for any tech stack using live web search and official documentation.

## What It Does

- Detects your project's tech stack by reading `package.json`, `go.mod`, `pyproject.toml`, and other standard files
- Fetches current best practices from official documentation (via Tavily + Context7)
- Generates `.claude/harness/<domain>.md` — quality standards for Claude to follow while working
- Generates linter config files (ESLint, Ruff, golangci-lint, Stylelint, etc.)
- Adds a `## Harness Standards` reference to your `CLAUDE.md`
- Audits code against harness standards at the end of each work session

## Commands

| Command | Purpose |
|---|---|
| `/harness-setup` | Initial setup — detect stack, fetch docs, generate harness and linter configs |
| `/harness-sync` | Update existing harness to reflect new dependencies or stack changes |
| `/harness-audit` | Check specific files against harness standards |

## Automatic Behavior

- **Session start**: detects if a harness exists and injects it as context
- **Session end**: lists files changed in the session and prompts harness review

## Generated Files (in your project)

```
your-project/
  CLAUDE.md                          ← gets a ## Harness Standards section added
  .claude/
    harness/
      <domain>.md                    ← quality standards for Claude
  eslint.config.js                   ← generated linter configs
  pyproject.toml                     ← [tool.ruff] section added
```

## Expanding Coverage

The plugin auto-detects common languages out of the box. For unlisted languages (e.g., Elixir, Swift), run `/harness-setup` — the plugin will ask you to describe your stack and generate a harness from web search.

To add permanent auto-detection for a language, open a PR to `plugins/harness-builder/scripts/stack_detector.py` and add an entry to `DETECTION_TABLE`.
