"""Re-entry guard for hook entry scripts.

When a hook spawns `claude -p` for an internal LLM call, the child Claude Code
instance fires the same plugin's hooks. Guard prevents that recursion by exiting
early when CLAUDE_WRITING_CONTEXT is set in the environment.

All `claude -p` spawns in this plugin must pass this env var to the child.
"""
import os
import sys


def exit_if_reentrant() -> None:
    if os.environ.get("CLAUDE_WRITING_CONTEXT"):
        sys.exit(0)
