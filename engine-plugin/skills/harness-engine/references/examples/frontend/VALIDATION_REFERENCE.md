# Frontend Validation Reference

프론트엔드 하네스가 최소한 아래 질문에 답할 수 있어야 한다.

## 필수 확인

- 서버 상태, 라우트 데이터, 폼 상태, 로컬 UI 상태를 어떻게 구분하는가
- `useEffect`가 허용되는 경우와 금지되는 경우를 어떻게 나누는가
- `TanStack Query`를 쓰는 경우 fetch, mutation, invalidate 규칙이 무엇인가
- `React Hook Form`을 쓰는 경우 default values와 reset 전략이 무엇인가
- 컴포넌트 경계와 import 경계를 어디서 끊는가
- FSD를 쓰는 경우 각 코드가 어느 layer/slice/public API에 속하는지 설명할 수 있는가
- FSD를 쓰는 경우 같은 layer cross-import를 어떻게 차단하거나 예외 처리하는가

## 구현 시작 전 체크

- `INDEX.md`, `ARCHITECTURE.md`, `ANTI_PATTERNS.md`, `VALIDATION.md` 묶음이 있는가
- Anti/Good 쌍이 문장형 요약만이 아니라 코드 예시까지 포함하는가
- 현재 스택의 공식 문서가 출처에 직접 적혀 있는가
- 테스트나 수동 검증 관찰 포인트가 `VALIDATION.md`에 적혀 있는가
- 세션 재개 시 어떤 문서를 먼저 읽어야 하는지 보이는가
- FSD를 채택했다면 public API, layer import rule, cross-import 방지 규칙이 `ARCHITECTURE.md`와 `ANTI_PATTERNS.md`에 직접 적혀 있는가
