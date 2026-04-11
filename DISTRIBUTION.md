# Distribution Guide

This guide covers how to distribute and install the engine plugin for Claude Code.

---

## For Users: Installing the Plugin

### Quick Install (2 commands)

```bash
# 1. Add this repository as a marketplace
claude plugin marketplace add nwleedev/engine

# 2. Install the engine plugin
claude plugin install engine@engine
```

That's it. The plugin is now active for all your Claude Code sessions.

### Verify Installation

```bash
# Check installed plugins
claude plugin list

# Or inside Claude Code, run:
/plugin
```

You should see the `engine` plugin with its skills (`/engine:deep-study`, `/engine:harness-engine`, etc.) and agents.

### Update

The plugin manager handles updates automatically. To manually check:

```bash
claude plugin update engine@engine
```

### Uninstall

```bash
claude plugin uninstall engine@engine
```

---

## For Teams: Auto-Prompt Installation

Add the marketplace to your project's `.claude/settings.json` so team members are automatically prompted to install:

```json
{
  "extraKnownMarketplaces": {
    "engine": {
      "source": { "source": "github", "repo": "nwleedev/engine" }
    }
  },
  "enabledPlugins": {
    "engine@engine": true
  }
}
```

When a team member opens the project and trusts it, Claude Code will automatically prompt them to install the engine plugin.

---

## For Organizations: Managed Settings

Use `strictKnownMarketplaces` in managed settings to enforce an allowlist of approved marketplaces across your organization:

```json
{
  "strictKnownMarketplaces": {
    "engine": {
      "source": { "source": "github", "repo": "nwleedev/engine" }
    }
  }
}
```

This prevents users from adding unapproved marketplaces while ensuring the engine plugin is available.

---

## Official Anthropic Marketplace

### Submission

Submit the plugin to the official Anthropic marketplace for maximum visibility:

- **Claude.ai**: [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
- **Console**: [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)

Once accepted, users can install with a single command:

```bash
claude plugin install engine
```

### Requirements

- `plugin.json` with all required fields (name, version, description, author)
- Quality and security review (specific criteria not publicly documented)
- Plugin name in kebab-case, no spaces

### Current Status

The plugin is available for self-hosted distribution. Official marketplace submission can be pursued for broader visibility.

---

## Distribution Options Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **GitHub marketplace** (self-hosted) | Immediate, no approval needed | Users must `marketplace add` first | Open source, small teams |
| **Team settings.json** | Auto-prompt, minimal friction | Per-project config needed | Internal teams |
| **Managed settings** | Org-wide enforcement | Requires admin access | Enterprises |
| **Official marketplace** | Discover tab, maximum visibility | Review required, timeline unclear | Wide distribution |

---

## Local Development

For testing changes during development:

```bash
# Load plugin directly without installation
claude --plugin-dir ./engine

# Reload after changes (inside Claude Code)
/reload-plugins
```

When `--plugin-dir` is used with the same name as an installed plugin, the local copy takes precedence for that session.

---

## Per-Project Configuration

After installation, users can customize plugin behavior by creating `.claude/engine.config` in their project:

```bash
# .claude/engine.config
REVIEW_AGENTS="domain,structure"         # Review perspectives
RESEARCH_PERSPECTIVES="pro,con"          # Research perspectives
REVIEW_THRESHOLD_SINGLE=2               # Single review threshold
REVIEW_THRESHOLD_MULTI=5                # Parallel review threshold
```

A template is included in the plugin at `engine.config.example`.
