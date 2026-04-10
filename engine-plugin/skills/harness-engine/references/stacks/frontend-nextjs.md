# Frontend Stack Seed: Next.js

## 목적

이 문서는 `frontend` task adapter를 사용할 때 프로젝트가 Next.js App Router 계열이면 추가로 확인해야 하는 seed reference를 정리한다.

이 문서는 조사 보조 자료다. 최종 규칙은 project contract packet에 기록한다.

## 추가 확인 항목

- Server Components와 Client Components 경계를 어디서 나누는가
- 페이지 진입 데이터가 Server Component, Route Handler, Server Action 중 어디에 있어야 하는가
- mutation 이후 revalidation 전략을 무엇으로 잡는가
- 브라우저 전용 API와 hydration 민감 로직을 어디에 두는가
- RHF/Zod 같은 클라이언트 폼 처리와 서버 액션 경계가 어떻게 나뉘는가
- Suspense, fallback, error boundary, streaming 전략이 packet에 기록되는가

## 기본 규칙

- 서버에서 해결 가능한 데이터 로딩은 Server Component 또는 서버 계층을 우선 검토한다.
- Client Component는 상호작용과 브라우저 상태에 집중한다.
- hydration mismatch를 피하기 위해 렌더 결과가 환경에 따라 달라지는 로직을 분리한다.
- cache/revalidate 전략은 Next.js 공식 문서 기준으로 확정한다.
- 폼과 검증 규칙은 contract packet에서 클라이언트/서버 경계를 함께 명시한다.

## 조사 시 우선 출처

- Next.js 공식 App Router 문서
- React 공식 Server Components / client boundaries 문서
- 사용하는 데이터 계층/폼/validator의 Next.js 연동 문서
