---
domain: react-frontend
language: auto
keywords: [component, tsx, jsx, hook, props, tailwind, state, query, useQuery, useForm]
file_patterns: ["*.tsx", "*.jsx", "src/components/**", "src/hooks/**", "src/pages/**"]
updated: 2026-04-18
---

# React Frontend Harness

## Purpose
This file defines the **ideal structure standard**, not the current project state.
Follow these rules during work. If existing code violates them, flag it.

## Core Rules

- [ ] No TypeScript `any` — use exact types or `unknown`
- [ ] Server state via Tanstack Query, client state via Zustand/Jotai
- [ ] `useEffect` for external system synchronization only
- [ ] Form input state via React Hook Form
- [ ] FSD layer dependency rules (upper → lower only)
- [ ] Do not manage state with `useRef` — use `useState` if UI must reflect changes

## Pattern Examples

### TypeScript Types

<Good>
```typescript
interface ApiResponse<T> { data: T; status: number; }
async function fetchUser(id: string): Promise<ApiResponse<User>> { ... }
```
Explicit generics guarantee type safety
</Good>

<Bad>
```typescript
async function fetchUser(id: any): Promise<any> { ... }
```
`any` — runtime errors not caught at compile time
</Bad>

---

### Server State Management

<Good>
```typescript
const { data: user, isLoading } = useQuery({
  queryKey: ['user', id],
  queryFn: () => fetchUser(id),
});
```
Automatic caching, retry, and loading state management
</Good>

<Bad>
```typescript
const [user, setUser] = useState(null);
useEffect(() => { fetchUser(id).then(setUser); }, [id]);
```
Manual fetch — no caching, error handling, or retry
</Bad>

---

### useEffect Overuse

<Good>
```typescript
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```
External system (event listener) synchronization — correct usage
</Good>

<Bad>
```typescript
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);
```
Derived state calculation — replace with `useMemo`
</Bad>

---

### No State Management via useRef

<Good>
```typescript
const [isOpen, setIsOpen] = useState(false);
```
State change triggers re-render
</Good>

<Bad>
```typescript
const isOpenRef = useRef(false);
isOpenRef.current = true; // no re-render → UI mismatch
```
</Bad>

## Anti-Pattern Gate

```
Using `any` type?                   → Replace with exact type
Deriving state in useEffect?        → Replace with useMemo/useCallback
Fetching directly without useQuery? → Replace with useQuery
Managing state with ref?            → Replace with useState/useReducer
Managing input with useState?       → Replace with React Hook Form
```
