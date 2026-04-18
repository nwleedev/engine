---
domain: react-frontend
language: auto
keywords: [컴포넌트, component, tsx, jsx, 훅, hook, props, tailwind, 상태, state, 쿼리, query]
updated: 2026-04-18
---

# React Frontend Harness

## 이 파일의 용도
현재 프로젝트 상태가 아닌 **이상적인 구조의 기준**입니다.
작업 중 이 기준을 준수하고, 기존 코드가 위반하면 지적하세요.

## 핵심 규칙

- [ ] TypeScript `any` 금지 — 정확한 타입 또는 `unknown` 사용
- [ ] 서버 상태는 Tanstack Query, 클라이언트 상태는 Zustand/Jotai
- [ ] `useEffect`는 외부 시스템 동기화 목적만 허용
- [ ] 입력 상태는 React Hook Form으로 관리
- [ ] FSD 레이어 의존성 규칙 준수 (상위 → 하위만 허용)
- [ ] `useRef`로 상태를 관리하지 않음 — UI 반영이 필요하면 `useState`

## 패턴 사례

### TypeScript 타입

<Good>
```typescript
interface ApiResponse<T> { data: T; status: number; }
async function fetchUser(id: string): Promise<ApiResponse<User>> { ... }
```
명시적 제네릭으로 타입 안전성 보장
</Good>

<Bad>
```typescript
async function fetchUser(id: any): Promise<any> { ... }
```
`any` — 런타임 오류를 컴파일 타임에 잡지 못함
</Bad>

---

### 서버 상태 관리

<Good>
```typescript
const { data: user, isLoading } = useQuery({
  queryKey: ['user', id],
  queryFn: () => fetchUser(id),
});
```
캐싱·재시도·로딩 상태 자동 관리
</Good>

<Bad>
```typescript
const [user, setUser] = useState(null);
useEffect(() => { fetchUser(id).then(setUser); }, [id]);
```
수동 fetch — 캐싱·에러·재시도 없음
</Bad>

---

### useEffect 남용

<Good>
```typescript
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```
외부 시스템(이벤트 리스너) 동기화 — 올바른 용도
</Good>

<Bad>
```typescript
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);
```
파생 상태 계산 — `useMemo`로 대체해야 함
</Bad>

---

### useRef 상태 관리 금지

<Good>
```typescript
const [isOpen, setIsOpen] = useState(false);
```
상태 변경 시 리렌더링 보장
</Good>

<Bad>
```typescript
const isOpenRef = useRef(false);
isOpenRef.current = true; // 리렌더링 없음 → UI 불일치
```
</Bad>

## 안티패턴 게이트

```
any 타입을 쓰려는가?           → 정확한 타입으로 교체
useEffect로 상태를 파생하는가? → useMemo/useCallback으로 교체
fetch를 직접 쓰는가?           → useQuery로 교체
ref로 상태를 관리하는가?       → useState/useReducer로 교체
입력값을 useState로 관리하는가? → React Hook Form으로 교체
```
