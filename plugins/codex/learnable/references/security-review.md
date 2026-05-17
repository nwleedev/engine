<!-- GENERATED FILE - DO NOT EDIT -->
<!-- source: plugin-sources/learnable/references/security-review.md -->

# Security Review

`verify-material` checks material and API output for:

- sensitive data in prompts, Markdown, events, audits, source refs, diagnostics, or provenance;
- path boundary violations and private material paths;
- prompt leakage from user request text into public-facing material;
- token leakage through URLs, headers, logs, local storage, Markdown, or JSON responses;
- unsafe source excerpts that quote too much copyrighted text or private repository content.

If any check fails, reject the material write or mark the material unverified. Do not repair by deleting requirements or weakening evidence standards.
