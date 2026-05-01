---
name: resume
description: Resume a prior Codex session by loading its INDEX.md context summary into the current session. Use when the user wants to recall, resume, or load context from previous Codex work in this project, or asks to see their saved sessions.
---

# Session Memory Resume

List or load saved sessions for the current project.

## Run

No argument — list sessions:

```
python3 "$(dirname "$0")/resume.py"
```

With 8-character session id prefix — inject INDEX into current session:

```
python3 "$(dirname "$0")/resume.py" <prefix>
```
