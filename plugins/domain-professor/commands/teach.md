---
description: Execute a task in professor mode and generate learning materials
---

Refer to the `domain-professor` skill and carry out the following task:

$ARGUMENTS

Processing order:
1. Identify the domain(s) involved in the task
2. Execute the task as described
3. For each domain encountered, create or update files under
   `.claude/textbooks/<domain>/` following the textbook file structure
   defined in the skill
4. Inform the user of the generated file paths and suggest the next
   learning step

If no task is specified, ask the user what they want to work on.
