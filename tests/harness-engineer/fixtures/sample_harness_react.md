---
domain: react-frontend
language: auto
keywords: [컴포넌트, component, tsx, jsx, 훅, hook, props, tailwind]
updated: 2026-04-18
---

# React Frontend Harness

## 핵심 규칙

- [ ] TypeScript `any` 금지
- [ ] 서버 상태는 Tanstack Query
- [ ] `useEffect`는 외부 동기화 목적만

## 패턴 사례

### TypeScript 타입

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

## 안티패턴 게이트

```
any 타입을 쓰려는가? → 정확한 타입으로 교체
```
