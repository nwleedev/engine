# Frontend Stack Seed: React SPA

## Purpose

This document compiles the additional seed reference to verify when using the `frontend` task adapter and the project is a React SPA.

This document is a research supplement. Final rules are recorded in the project contract packet.

## Additional Verification Items

- Is route entry data properly placed in React Router loader/clientLoader
- Do Query cache and route data responsibilities not conflict in the CSR environment
- Is the invalidate/revalidate flow after mutations documented
- Are browser-only state and server state separated
- Does the entry point for form/validation combinations like RHF and Zod converge to a single location
- Are Suspense, fallback, and error boundary strategies recorded in the packet

## Default Rules

- For page entry data, first consider React Router loader/clientLoader.
- For server state, prioritize server state tools like TanStack Query.
- Do not unnecessarily elevate local state created by browser interactions to server state or global state.
- Do not tie network flows to `useEffect`.
- Form default values and validation rules specify `defaultValues`/`values`/`reset` and resolver connections in the contract packet.

## Priority Sources for Research

- React Router official documentation
- React official documentation
- Official documentation for the server state/form/validator in use
