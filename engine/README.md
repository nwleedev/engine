# engine

Claude Code Harness System — plan enforcement, quality gates, domain knowledge, and session continuity.

See the [full documentation](../README.md) for installation, usage, and configuration.

## Plugin Structure

```
engine/
├── .claude-plugin/plugin.json   Plugin manifest
├── agents/                      Sub-agent definitions
├── commands/                    Slash command entry points (/engine:<name>)
├── hooks/
│   ├── hooks.json               Hook event configuration
│   └── scripts/                 Hook-invoked shell scripts
│       └── lib/                 Shared shell library (source-only)
├── skills/                      Engine skills
└── templates/                   Project template files (.example)
```

## Agents

| Agent | Role |
|---|---|
| `domain-professor` | Interactive domain teaching from scratch |
| `harness-researcher` | Domain investigation and harness generation |
| `plan-readiness-checker` | Deep analysis of plan execution readiness |
| `project-researcher` | External evidence research with perspective dispatch |
| `turn-summarizer` | Narrative context summary at session end |
| `work-reviewer` | Independent quality review after task completion |

## Skills / Commands

| Skill | Command | Description |
|---|---|---|
| `setup` | `/engine:setup` | Initialize CLAUDE.md, engine.env, .gitignore |
| `completion-gate` | `/engine:completion-gate` | Iron Law verification gate |
| `deep-study` | `/engine:deep-study` | Systematic domain learning |
| `harness-engine` | `/engine:harness-engine` | Create/enhance harness skills |
| `research-methodology` | `/engine:research-methodology` | Evidence-based research |
| `socratic-thinking` | `/engine:socratic-thinking` | Explore-first thinking principles |
| `failure-response` | `/engine:failure-response` | Structured failure handling |

## License

MIT — see [LICENSE](LICENSE)
