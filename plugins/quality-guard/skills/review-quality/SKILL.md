---
description: Review auto-detected quality issues in raw.md, approve or reject each, and reset the pending count
---

Argument: $ARGUMENTS

Steps:

1. Read `.claude/feedback/raw.md`. If the file does not exist or contains no `[auto-detected]` entries, output: "No pending auto-detected quality issues." and stop.

2. Extract all entries tagged `[auto-detected]` from raw.md. Display them numbered:
   ```
   [1] ts: <timestamp>
       text: "[auto-detected] <reason> (Q: '<question snippet>')"
   ```

3. For each item, ask the user: "Approve (add to feedback) or Reject (delete)?" — or accept a batch decision if $ARGUMENTS is "approve-all" or "reject-all".

4. Processing:
   - **Approve**: keep the entry in raw.md as-is (it will be included in the next compression run).
   - **Reject**: remove the entry block (the `---\nts: ...\ntext: ...\n---` block) from raw.md entirely.

5. After processing all items:
   - If any entries were approved: output "N item(s) approved. They will be included in the next quality compression."
   - If all entries were rejected: output "All auto-detected items rejected. No feedback recorded."
   - Write the count of remaining `[auto-detected]` entries (after rejections) to `.claude/quality/pending_review.txt`.
   - If the count is 0: delete `.claude/quality/pending_review.txt` instead of writing "0".

6. Confirm completion in one sentence.
