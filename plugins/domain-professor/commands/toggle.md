---
description: Toggle professor learning mode on or off for this session
---

Toggle professor mode for this session.

Steps:
1. Find the project root:
   `git rev-parse --show-toplevel 2>/dev/null || echo "$PWD"`

2. Construct a JSON payload using your current session ID and the project root,
   then pipe it to the toggle script:
   ```
   echo '{"cwd":"<project_root>","session_id":"<your_session_id>"}' \
     | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/toggle_state.py
   ```

3. Report the result:
   - Output `active`   → "Professor mode ON. Learning mode is now active for this session."
   - Output `inactive` → "Professor mode OFF. Learning mode has been disabled."
