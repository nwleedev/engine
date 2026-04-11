# Frontend Validation Reference

A frontend harness must be able to answer at least the following questions.

## Required Checks

- How do you distinguish between server state, route data, form state, and local UI state
- How do you differentiate between cases where `useEffect` is allowed and where it is prohibited
- If using `TanStack Query`, what are the fetch, mutation, and invalidate rules
- If using `React Hook Form`, what are the default values and reset strategies
- Where do you draw component boundaries and import boundaries
- If using FSD, can you explain which layer/slice/public API each piece of code belongs to
- If using FSD, how do you block or handle exceptions for same-layer cross-imports

## Pre-Implementation Check

- Do you have the `INDEX.md`, `ARCHITECTURE.md`, `ANTI_PATTERNS.md`, `VALIDATION.md` bundle
- Do Anti/Good pairs include code examples, not just sentence-form summaries
- Are the official documentation sources for the current stack directly listed in the references
- Are test or manual verification observation points documented in `VALIDATION.md`
- Is it visible which documents should be read first when resuming a session
- If FSD is adopted, are the public API, layer import rules, and cross-import prevention rules directly documented in `ARCHITECTURE.md` and `ANTI_PATTERNS.md`
