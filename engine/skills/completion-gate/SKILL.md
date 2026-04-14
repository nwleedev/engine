---
name: completion-gate
description: "Enforce verification before claiming completion. The Iron Law: fresh verification evidence must exist before any completion claim."
user-invocable: true
---

# Completion Gate

**The Iron Law**: 완료를 주장하기 전에 신선한 검증 증거가 있어야 한다.
(Before claiming completion, fresh verification evidence must exist.)

---

## Gate Function

Before claiming any task, feature, or step is complete, execute these 5 steps in order:

1. **IDENTIFY** — What command or check proves this claim is true?
   - Name the exact command, file read, or tool call that would demonstrate completion
   - If you cannot name it, you cannot claim completion

2. **RUN** — Execute the full verification now
   - No cached results, no "I ran it earlier", no assumed success
   - Run it fresh in this turn

3. **READ** — Examine the full output
   - Read the entire output, not just the last line
   - Check the exit code (for commands: 0 = success, non-zero = failure)

4. **VERIFY** — Does the output actually support the claim?
   - The output must directly demonstrate the specific claim being made
   - "Tests passed" requires: test output showing 0 failures
   - "File modified" requires: reading the file and seeing the change
   - "Hook active" requires: log entry confirming the hook fired

5. **ONLY THEN** — Make the completion claim
   - State what evidence was observed
   - Quote or reference the specific output that proves the claim

---

## Common Failures

| Completion Claim | What Fresh Evidence Looks Like |
|-----------------|-------------------------------|
| "Tests pass" | Test command output: `0 failures`, `X passed` |
| "File modified correctly" | Read tool output showing the changed content |
| "Hook is active" | Hook trigger log in `.harness-usage` or hook stderr |
| "Harness matched" | `.harness-usage` file containing `[MATCH]` entry |
| "Script runs without error" | Shell command exit code 0 + stdout/stderr checked |
| "Configuration applied" | Read of config file showing the new value |
| "Commit was made" | `git log --oneline -1` output with the commit message |

---

## Anti-patterns

These are NOT completion evidence:
- "I wrote the code, so it should work"
- "The logic looks correct to me"
- "I ran it earlier in this session"
- "The previous step succeeded so this one must have too"
- Summarizing what you intended to do instead of what you observed

---

## When to Invoke

Invoke this skill (or apply its Gate Function inline) before:
- Reporting a task, step, or change as complete
- Moving to the next task in a multi-step plan
- Declaring a bug fixed
- Claiming a feature is working
