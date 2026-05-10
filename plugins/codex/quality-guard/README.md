# codex-quality-guard

`codex-quality-guard` is a Codex plugin for checking whether a work turn ended with superficial work.

It does not use Codex hooks. Instead, it provides reusable skills and AGENTS.md guidance:

- `codex-quality-guard:retrospect` reviews the current turn for superficial work.
- `codex-quality-guard:install` checks whether AGENTS.md contains the recommended retrospective rule block.

## Skills

### `codex-quality-guard:retrospect`

Use this before finalizing a work turn, especially after code or file changes.

The skill reports:

```text
Context status: complete | reconstructed | incomplete
Superficial risk: none | low | medium | high | unknown
Evidence sources:
- current conversation: used | unavailable
- AGENTS.md: used | unavailable
- project artifacts: used | unavailable
- git status/diff: used | unavailable
- user-provided summary: used | unavailable
- optional session memory: used | unavailable | mismatch
Evidence:
- ...
Root-cause check:
- ...
Next action:
- ...
```

`retrospect` is not a replacement for Codex `/review`. `/review` reviews a diff for defects. `retrospect` reviews the current turn's working pattern.

### `codex-quality-guard:install`

Use this to inspect AGENTS.md:

```bash
python3 /path/to/codex-quality-guard/skills/install/install.py
```

The command prints one of these statuses:

- `installed`
- `partial`
- `missing`
- `not found`

The installer is diagnostic-only. It prints a recommended block but does not edit AGENTS.md.
