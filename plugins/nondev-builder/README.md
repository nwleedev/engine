# nondev-builder

A Claude Code plugin that enables professional non-development work (market research,
stock analysis, PRD writing, pitch decks, and more) through domain-agnostic methodology
injection, parallel web research, and independent output evaluation.

## What it does

- **`/nondev-setup [task-name|description]`** — Runs a 6-item brainstorming loop, fetches
  current best practices via parallel web search, and generates three artifacts per domain:
  - `.claude/nondev/<task-name>/skill.md` — Domain methodology (B layer)
  - `.claude/nondev/<task-name>/rubric.md` — Evaluation rubric (C layer)
  - `.claude/commands/<task-name>.md` — Task workflow slash command (A+B+C)
- **`/<task-name> [goal]`** — Executes the professional workflow: methodology injection →
  3 parallel research subagents → synthesis → independent evaluator subagent
- **`/nondev-sync <task-name>`** — Refreshes regenerable sections without touching
  user-edited sections (`Source Collection Strategy`, `Custom Examples`)
- **SessionStart hook** — Lists configured domains on session start (1 file read, O(1))
- **UserPromptSubmit hook** — Suggests relevant command when prompt matches keywords
- **Stop hook** — Injects rubric evaluation reminder after each turn

## Key design principles

- **Zero hardcoding**: Plugin files contain no domain names, keywords, or rubric items
- **Scalable hooks**: Session start and prompt matching always read only `index.json` (O(1))
- **Two-world model**: Plugin files (version-controlled, domain-agnostic) vs. generated
  files (project-scoped, committable for team sharing)
- **Source enforcement**: Every figure in the output must cite an external source
- **Independent evaluation**: Evaluator subagent runs in isolated context (no self-review bias)

## Getting started

```bash
/nondev-setup market-research
# or with a natural language description:
/nondev-setup "주식 시장 단기 투자를 위한 종목 분석이 필요합니다"
```

After setup:
```bash
/market-research "국내 SaaS 시장 규모 및 경쟁 현황 분석"
```

## Generated file layout

```
<your-project>/
└── .claude/
    ├── nondev/
    │   ├── index.json                  # domain matching index (O(1) reads)
    │   └── <task-name>/
    │       ├── skill.md                # domain methodology
    │       └── rubric.md               # evaluation rubric
    └── commands/
        └── <task-name>.md              # task workflow slash command
```
