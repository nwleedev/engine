---
name: install
description: Use when verifying whether AGENTS.md contains the recommended codex-quality-guard diagnostic rules.
---

# Codex Quality Guard Install

Inspect the current project's AGENTS.md for codex-quality-guard rules.

## Run

```bash
python3 /path/to/codex-quality-guard/skills/install/install.py
python3 /path/to/codex-quality-guard/skills/install/install.py ko
```

## Status Meanings

- `installed`: AGENTS.md contains the recommended diagnostic rules.
- `partial`: AGENTS.md contains some, but not all, required markers.
- `missing`: AGENTS.md exists but does not contain the required markers.
- `not found`: AGENTS.md was not found at the resolved project root.

## Diagnostic Only

This installer is diagnostic-only. It prints status, missing markers, guidance, and a recommended block, but it does not edit AGENTS.md.

Do not edit AGENTS.md unless the user explicitly asks to apply the recommended block.
