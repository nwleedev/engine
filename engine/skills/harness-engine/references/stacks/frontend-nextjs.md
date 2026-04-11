# Frontend Stack Seed: Next.js

## Purpose

This document compiles the additional seed reference to verify when using the `frontend` task adapter and the project is a Next.js App Router variant.

This document is a research supplement. Final rules are recorded in the project contract packet.

## Additional Verification Items

- Where do you draw the boundary between Server Components and Client Components
- Should page entry data live in a Server Component, Route Handler, or Server Action
- What revalidation strategy do you use after mutations
- Where do you place browser-only APIs and hydration-sensitive logic
- How is the boundary drawn between client form handling (RHF/Zod) and server actions
- Are Suspense, fallback, error boundary, and streaming strategies recorded in the packet

## Default Rules

- For data loading that can be resolved on the server, prioritize Server Components or the server layer.
- Client Components focus on interactivity and browser state.
- To avoid hydration mismatches, separate logic whose render output varies by environment.
- Confirm cache/revalidate strategies based on Next.js official documentation.
- Form and validation rules specify the client/server boundary together in the contract packet.

## Priority Sources for Research

- Next.js official App Router documentation
- React official Server Components / client boundaries documentation
- Next.js integration documentation for the data layer/form/validator in use
