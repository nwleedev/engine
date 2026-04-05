# Frontend Adapter

## 목적

harness-engine이 프론트엔드 도메인 하네스를 생성하거나 보강할 때, 공통 `research` phase 이후 이 어댑터를 로드하여 프론트엔드 고유의 **최소 계약**을 적용한다.

이 문서는 모든 프론트엔드 프로젝트에 공통으로 필요한 하한선을 정의한다. 실제 프로젝트의 세부 스택 조합은 세션 contract packet에서 닫는다.

## Coverage Contract

프론트엔드 하네스에는 다음 항목이 반드시 포함되어야 한다. 누락 시 하네스가 불완전한 것으로 판정한다.

### 필수 축 (모든 프론트엔드 프로젝트)

1. **상태 관리 분류 기준**
   - 서버 상태, 라우트 진입 데이터, 폼 상태, 글로벌 UI 상태, 로컬 UI 상태의 구분 기준
   - 각 상태 유형에 대한 도구 선택 규칙
2. **데이터 진입/변경 규칙**
   - 데이터 fetch 진입점 규칙
   - mutation 후 invalidate/revalidate 규칙
   - 캐시 책임 분리
3. **폼 처리 규칙**
   - 폼 상태의 단일 진실 공급원
   - 초기값 주입 전략
   - 유효성 검증 진입점
4. **부수 효과(useEffect) 사용 기준**
   - 허용 케이스와 금지 케이스의 명확한 분류
   - 금지 케이스별 대체 방법
5. **컴포넌트/레이어 경계**
   - 폴더/레이어 구조 규칙
   - import 경계 규칙
   - props 전달 기준과 대안

### 프로젝트 contract packet에서 반드시 조사할 항목

다음 항목은 어댑터에 고정하지 않고, 매 프로젝트 contract packet에서 직접 닫는다.

- 아키텍처 스타일이 일반 layered/component 구조인지, Feature Sliced Design(FSD)인지
- React SPA인지 Next.js App Router인지
- React Router DOM 또는 Next.js의 데이터 진입 규칙
- TanStack Query 사용 여부와 query/mutation/invalidation 전략
- React Hook Form 사용 여부와 `defaultValues` / `values` / `reset` 선택 기준
- Zod 또는 대체 validator 사용 여부와 schema/resolver 연결 규칙
- Suspense / fallback / error boundary 전략
- 접근성(a11y), i18n, 성능, 테스트가 필수인지 여부

## 1차 근거 소스

프론트엔드 하네스의 규칙은 다음 소스를 1차 근거로 사용한다. 실제 조합은 contract packet에서 좁힌다.

- React 공식 문서 (react.dev)
- 사용 중인 라우터 공식 문서 (React Router, Next.js, Remix 등)
- 사용 중인 서버 상태 도구 공식 문서 (TanStack Query 등)
- 사용 중인 폼 라이브러리 공식 문서 (React Hook Form 등)
- 사용 중인 validator 공식 문서 (Zod 등)
- Feature-Sliced Design 공식 문서 (채택 시)
- MDN Web Docs

선택형 보조 도구:

- Context7 MCP
  - 공식 문서 스니펫 검색을 빠르게 보강할 수 있다.
  - 단, 최종 규칙과 인용은 원문 공식 문서로 다시 확인한다.

스택별 seed reference는 `stacks/<stack>.md`에서 정의한다.

## 선택형 Example Pack

프론트엔드 task adapter는 아래 example pack을 참고할 수 있다.

- `references/examples/frontend/README.md`
- `references/examples/frontend/ANTI_GOOD_REFERENCE.md`
- `references/examples/frontend/VALIDATION_REFERENCE.md`

규칙:

- example pack은 규범 계약이 아니라 reference-only evidence다.
- example pack이 없어도 adapter 자체는 유효하다.
- example pack이 있다면 contract packet과 충돌하지 않는지 확인한다.

## 조건부 아키텍처 규칙: Feature Sliced Design

프로젝트 contract packet에서 아키텍처 스타일이 Feature Sliced Design(FSD)로 확정되면 아래 규칙을 추가 적용한다.

### FSD에서 반드시 드러나야 하는 항목

- 사용하는 레이어 범위 (`app`, `pages`, `widgets`, `features`, `entities`, `shared`)
- 해당 프로젝트에서 실제로 사용하는 layer만 유지한다는 원칙
- layer import rule: 상위 layer는 하위 layer만 import
- `app`과 `shared`는 slice가 없는 예외 layer로 취급
- slice 외부에서는 내부 구현이 아니라 public API를 통해 접근
- 같은 layer의 서로 다른 slice 간 cross-import는 기본적으로 code smell로 본다

### FSD 채택 시 contract packet에 반드시 기록할 항목

- `architecture_style: fsd`
- 실제 사용하는 layer 목록
- public API 정책 (`index.ts` 또는 동등한 공개 진입점)
- cross-import 예외 허용 여부
- `@x` cross-reference 같은 예외 메커니즘 사용 여부
- feature/widget 조립 책임을 어느 상위 layer에서 닫는지

## Anti/Good 최소 필수 쌍 목록

프론트엔드 하네스의 ANTI_PATTERNS.md에는 다음 케이스 각각에 대해 Anti와 Good 쌍이 **반드시** 존재해야 한다. 한쪽만 있으면 불완전 상태로 판정한다.

### 상태 관리

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 서버 상태 복제 | 서버 데이터를 로컬 상태에 복제 저장 | 서버 상태 도구에서 직접 구독 |
| 상태 도구 오용 | 서버/폼/라우트 데이터를 글로벌 상태에 저장 | 각 상태 유형에 맞는 도구 사용 |

### 데이터 흐름

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| useEffect fetch | useEffect로 데이터 fetch | 라우터 데이터 진입점 또는 Query 사용 |
| mutation 후 수동 동기화 | mutation 성공 후 로컬 상태 수동 패치 | invalidate/revalidate 사용 |
| 라우트 데이터-쿼리 중복 | 같은 진입 데이터를 loader와 query로 중복 fetch | 라우트 진입 책임과 쿼리 책임을 분리 |

### 폼/검증

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 초기값 분산 주입 | useEffect + setValue 반복으로 초기값 주입 | `defaultValues`, `values`, 또는 명시적 `reset` 전략 사용 |
| 폼 상태 중복 | 폼 값을 로컬 상태에 별도 저장 | 폼 라이브러리를 단일 진실 공급원으로 사용 |
| 검증 분산 | 입력 검증을 컴포넌트별 조건문으로 분산 | schema + resolver 등 단일 검증 진입점 사용 |
| 타입/런타임 검증 불일치 | 타입 정의와 런타임 검증 규칙이 따로 논다 | schema 기준으로 타입/런타임 경계 정렬 |

### 컴포넌트 설계

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| props drilling | 2단계 이상 props 전달 | context, store, route data 등 대안 사용 |
| 레이어 경계 위반 | 하위 레이어가 상위 레이어 import | 레이어 규칙에 따른 단방향 의존 |
| FSD public API 우회 | 다른 slice의 `model/internal` 같은 내부 경로 직접 import | slice의 공개 public API만 import |
| FSD cross-import 남용 | 같은 layer의 다른 slice를 직접 참조해 흐름 결합 | 상위 layer 조립, slice 병합, entities 하향 이동, 또는 합의된 public API 전략 사용 |

### useEffect / Suspense

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 파생 값 동기화 | props/state에서 계산 가능한 값을 effect로 state에 저장 | render 계산 또는 필요한 경우에만 memoization |
| 이벤트 처리 | 사용자 이벤트를 effect로 처리 | event handler 직접 사용 |
| Suspense 경계 부재 | 비동기 렌더링 구간에 fallback/error boundary 전략이 없음 | packet에 맞는 Suspense/fallback/error boundary 경계 명시 |

**주의**: 위 목록은 최소 필수 쌍이다. 실제 프로젝트는 contract packet에서 추가 쌍을 더 정의한다.

## 드라이런 입출력 예시

### Positive Case: 상태 관리 분류 검증

**Input**: "사용자 프로필 데이터를 화면에 표시하고, 사용자가 프로필을 수정할 수 있는 폼을 제공해야 한다."

**Expected Output (하네스가 안내해야 하는 방향)**:

- 프로필 표시 데이터 → 서버 상태 또는 라우트 진입 데이터
- 프로필 수정 폼 → 폼 상태
- 폼 초기값 → packet에 맞는 `defaultValues`/`values`/`reset` 전략
- 저장 요청 → mutation + invalidate/revalidate

### Negative Case: useEffect 남용 감지

**Input**: "API에서 데이터를 가져와서 state에 저장한 후 화면에 표시한다."

**Expected Output (하네스가 차단해야 하는 패턴)**:

- useEffect 내 fetch → 금지 케이스로 감지
- state에 저장 → 서버 상태 복제로 감지
- 대안 제시: 라우트 진입점 또는 TanStack Query

## 스택 분기

프론트엔드 도메인 내 기술스택에 따라 추가 지침이 필요하다.

스택 감지 순서:

1. 프로젝트 루트의 AGENTS.md / CLAUDE.md에서 스택 선언 확인
2. 선언이 없으면 package.json 확인 (`next`, `react-router-dom`, `remix`, `astro` 등)
3. 선언도 없고 감지도 불가능하면 사용자에게 스택 선택을 요청

스택별 seed reference 파일:

- `stacks/frontend-nextjs.md`
- `stacks/frontend-react-spa.md`

stack 파일은 seed reference일 뿐이다. 실제 프로젝트 규칙은 contract packet에서 확정한다.

## 아키텍처 스타일 분기

프론트엔드 도메인 내에서는 기술 스택과 별개로 아키텍처 스타일 분기가 필요할 수 있다.

예:

- 일반 layered/component 구조
- Feature Sliced Design

아키텍처 스타일은 stack seed와 별도로 contract packet에서 명시한다. FSD가 선택된 경우 FSD 공식 문서를 1차 근거에 추가하고, `ARCHITECTURE.md`, `ANTI_PATTERNS.md`, `VALIDATION.md`에 public API, layer rule, cross-import 방지 규칙이 보여야 한다.

## Enforcement (강제 규칙 설정)

프론트엔드 하네스 생성 시, ANTI_PATTERNS.md의 안티패턴 중 ESLint로 자동 검출 가능한 항목을 `enforcement/LINT_RULES.md`에 매핑한다.

### 필수 ESLint 플러그인

스택에 따라 다음 플러그인을 기본으로 포함한다:

- **공통**: `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-plugin-import`
- **TypeScript**: `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`
- **Next.js**: `eslint-config-next` (`next/core-web-vitals` 또는 `next/recommended`)
- **TanStack Query**: `@tanstack/eslint-plugin-query`

### 안티패턴 → ESLint 규칙 매핑 예시

| 안티패턴 | ESLint 규칙 | 심각도 |
|---------|------------|--------|
| useEffect fetch | 커스텀 규칙 또는 TanStack Query 플러그인 | error |
| exhaustive-deps 무시 | `react-hooks/exhaustive-deps` | error |
| import 순서 불일치 | `import/order` | warn |
| 미사용 변수 | `@typescript-eslint/no-unused-vars` | error |
| any 타입 남용 | `@typescript-eslint/no-explicit-any` | error (strict) / warn (moderate) |

### 강도 기준

contract packet의 `enforcement_severity`에 따라:

- **strict**: 위 규칙 대부분 `error`. `next/core-web-vitals` 기반. 추가 접근성/성능 규칙 포함.
- **moderate**: 핵심 안티패턴만 `error`, 스타일 관련은 `warn`.
- **minimal**: 핵심 안티패턴만 `warn`, 나머지 비활성화.

## 스킬 내부 reference example

- `references/examples/frontend/*`에는 현재 저장소의 레거시 프론트엔드 자료와 직접 예시에서 추린 reference-only evidence가 있다.
- 이 예시는 문서 구조, Anti/Good 직접성, validation 강도의 기준을 보여주기 위한 것이며, 새 프로젝트에 그대로 복사할 규칙이 아니다.
- 현재 프로젝트 스택과 맞지 않는 예시는 참고만 하고 portable core 규칙으로 승격하지 않는다.

## 설계 근거

- Coverage Contract 필수 축: React/라우터/상태관리/폼 계층에서 반복적으로 필요한 최소 판단 축
- 프로젝트별 stack/library 계약: 공식 문서를 project contract packet으로 재조합하는 구조
- FSD 조건부 규칙: FSD 공식 레이어/슬라이스/Public API/cross-import 가이드 기반
- Anti/Good 필수 쌍 구조: OpenAI GPT-5 Prompting Guide의 XML-Tagged Instruction Blocks + Addyosmani 3-Tier Boundary System
