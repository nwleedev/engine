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

5. **Fetch the source.**

   **Stage 1 — Python script (urllib):**
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

   Use the Bash tool to run this command. If it exits 0, proceed to Step 6.

   If it exits non-zero due to a network/access failure (stderr contains
   "Error:" related to the URL), do NOT stop — proceed to Stage 2.
   For any other non-zero exit (bad arguments, path escapes refs dir, etc.),
   stop and show the error.

   **Stage 2 — Tavily extract (if Tavily MCP is available):**
   Use the `mcp__tavily-mcp__tavily_extract` tool:
   ```
   urls=["<url>"], format="markdown"
   ```
   On success: write the returned markdown text to `/tmp/ref_<name>.md` (where `<name>` is the value confirmed in Step 2)
   using the Write tool, then call the handler script:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/add_ref_handler.py" \
     "/tmp/ref_<name>.md" \
     --name "<name>" \
     --topic "<topic>" \
     [--tags tag1 tag2 ...]
   ```
   If the handler script exits 0, proceed to Step 6. If it exits non-zero for a reason other than network/access, stop and show the error. If Tavily MCP is unavailable or the Tavily call fails, proceed to Stage 3.

   **Stage 3 — Playwright MCP (if Playwright MCP is available):**
   Use the `mcp__plugin_playwright_playwright__browser_navigate` tool with `url="<url>"`,
   then use `mcp__plugin_playwright_playwright__browser_evaluate` with:
   ```
   function="() => document.body.innerText"
   ```
   IMPORTANT: Do NOT pass a `filename` parameter to either tool. Playwright
   MCP writes files to its own `.playwright-mcp/` output directory — not to
   `.claude/refs/`. Capture the return value as text only.

   Write the returned text to `/tmp/ref_<name>.md` using the Write tool,
   then call the handler script the same way as Stage 2. If it exits 0, proceed to Step 6.

   **Full documentation crawl (opt-in):**
   If the user explicitly requests collecting the full documentation site
   (not just one page), use the `mcp__tavily-mcp__tavily_crawl` tool:
   ```
   url="<base_url>", max_depth=2, select_paths=["/docs/.*"], limit=50, format="markdown"
   ```
   Write each page's content as a separate file under the topic folder.
   Default behavior is always single-page.

   **All stages fail:**
   Stop. Report the error. Do NOT create stub, placeholder, or
   AI-generated content files as a substitute for the real source.

6. **Report the result.**
   - On success (exit code 0): the script prints the registered relative path.
     Output: "Reference '<name>' registered at `<path>`. Added to `.claude/refs/INDEX.md`."
   - On failure (non-zero exit): show the stderr output to the user and stop.
     Do not attempt to retry or fix the error automatically.

**Important constraints:**
- Do NOT read the fetched file or summarise its contents.
- Do NOT make any additional network requests or tool calls on the file content.
- Do NOT modify the file after it is saved.
- NEVER create stub, placeholder, or AI-generated content files when a source
  is inaccessible. If all fetch stages fail, stop and report the error.
- When using Playwright MCP tools, NEVER use the `filename` parameter.
  Always capture content as a text return value and write it yourself
  using the Write tool. The `filename` parameter writes to Playwright's
  own output directory, not to `.claude/refs/`.
