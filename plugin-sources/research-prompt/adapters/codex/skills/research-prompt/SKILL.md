---
name: research-prompt
description: Generate a ChatGPT Deep Research Markdown prompt from live project context without calling external APIs.
---

# Research Prompt

## Purpose

Create one ChatGPT Deep Research Markdown prompt from live project context without calling external APIs. The skill is stack-agnostic: inspect the project signals that exist instead of assuming one language, framework, or runtime.

## When to use

- When a user needs a source-backed Deep Research prompt about a codebase, failure, migration, architecture, or implementation question.
- When the prompt should include selected files, logs, reproduction steps, constraints, goals, or expected output.
- When the task needs one portable Markdown artifact, not live research execution.

## Inputs to inspect

- User-provided `--problem`, `--path`, `--log`, `--repro`, `--constraint`, `--goal`, and `--expected-output` values.
- Helper-collected root dependency files, lockfiles, Dockerfiles, git diff, user-provided paths, logs, stack traces, and symbol candidates.
- Other explicit files, tests, configs, manifests, and deployment files that the user names or that are visible project signals.
- Project boundaries and denied paths so secrets, credentials, and outside-project files are not included.

## Stack detection rules

These rules are guidance for choosing user-provided paths, logs, symbols, and visible project signals. They are not a promise that the helper automatically analyzes every stack or fully walks each ecosystem.

- Node/TypeScript: inspect `package.json`, lockfiles, `tsconfig`, source files, test config, and framework config.
- Python: inspect `pyproject.toml`, requirements files, source packages, tests, and tooling config.
- Java/Kotlin: inspect Gradle or Maven files, source sets, tests, and framework config.
- Go: inspect `go.mod`, `go.sum`, packages, `_test.go` files, and build tags.
- Rust: inspect `Cargo.toml`, `Cargo.lock`, crates, tests, features, and toolchain config.
- Docker/Kubernetes: inspect Dockerfiles, Compose files, Helm charts, Kustomize overlays, and Kubernetes manifests.

## Run

Use the helper script next to this skill:

```bash
python3 plugins/codex/research-prompt/skills/research-prompt/scripts/research_prompt.py --harness codex --problem "<research question>" --path <relative-path>
```

Run it from the project root. The helper uses the current working directory as
`--project-root` and today's date for the output file when those arguments are
not supplied. If the plugin is installed outside this repository, replace
`plugins/codex/research-prompt` with that installed plugin root.

## Output

The helper writes exactly one Markdown prompt under:

```text
.codex/deep-research-prompts/
```

## Do not

- Do not create metadata, cache, index, latest, or database files.
- Do not include secrets, credentials, private data, or denied file contents.
- Do not read outside-project paths; record the denial reason in the prompt instead.
- Do not assume the project stack before inspecting available project signals.
