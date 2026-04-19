---
domain: react-frontend
language: auto
keywords: [component, tsx, jsx, hook, props, tailwind]
file_patterns: ["*.tsx", "*.jsx", "src/components/**", "src/hooks/**"]
updated: 2026-04-18
---

# React Frontend Harness

## Core Rules

- [ ] No TypeScript `any` — use exact types or `unknown`
- [ ] Server state via Tanstack Query
- [ ] `useEffect` for external synchronization only

## Pattern Examples

### TypeScript Types

<Good>
```typescript
interface User { id: string; name: string; }
```
</Good>

<Bad>
```typescript
const user: any = fetchUser();
```
</Bad>

## Anti-Pattern Gate

```
Using `any` type? → Replace with exact type
```
