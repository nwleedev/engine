---
name: add-ref
description: Add an external reference (URL or local file) to the project's refs index
---

Argument: $ARGUMENTS

Adds a URL or local file path to `.claude/refs/` and registers it in the INDEX so Claude
can consult it in future sessions. Does NOT read, summarise, or analyse the file content.

Steps:

1. **Determine the source.**
   - If $ARGUMENTS is non-empty and looks like a URL (starts with `http://` or `https://`)
     or a file path (absolute or starts with `./`, `../`, or `/`): use it as the source.
   - Otherwise: ask the user — "What URL or file path do you want to add as a reference?"
     Wait for the answer before continuing.

2. **Ask for a short name.**
   Suggest one based on the URL hostname or filename (e.g., for `https://docs.python.org/3/library/typing.html`
   suggest `python-typing`; for `/home/user/report.pdf` suggest `report`).
   Ask: "What name should this reference have? [suggested: <suggestion>]"
   Use the user's answer (or the suggestion if they press Enter / confirm).

3. **Ask for a topic folder.**
   Ask: "What topic folder should this be stored under? (e.g., python, architecture, api)"
   Use the user's answer as the `--topic` argument. Do not create the folder yourself — the
   script will create it.

4. **Ask for tags (optional).**
   Ask: "Any tags? (space-separated, e.g., python typing stdlib — or press Enter to skip)"
   If the user provides tags, split them by whitespace. If the user skips, use no tags.

5. **Run the handler script.**
   Construct the command using `CLAUDE_PLUGIN_ROOT` for the script path. Build `--tags`
   arguments from the tags list (one `--tags` flag followed by space-separated tags, or omit
   entirely if no tags). Do NOT include `--cwd`; the script resolves the project root from
   `CLAUDE_PROJECT_DIR` or the current working directory automatically.

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/add_ref_handler.py" \
     "<source>" \
     --name "<name>" \
     --topic "<topic>" \
     [--tags tag1 tag2 ...]
   ```

   Use the Bash tool to run this command.

6. **Report the result.**
   - On success (exit code 0): the script prints the registered relative path.
     Output: "Reference '<name>' registered at `<path>`. Added to `.claude/refs/INDEX.md`."
   - On failure (non-zero exit): show the stderr output to the user and stop.
     Do not attempt to retry or fix the error automatically.

**Important constraints:**
- Do NOT read the fetched file or summarise its contents.
- Do NOT make any additional network requests or tool calls on the file content.
- Do NOT modify the file after it is saved.
