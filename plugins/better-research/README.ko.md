# better-research

Claude Code에서 구조화된, 편향 저항성 리서치를 강제합니다. 두 개의 훅을 등록하여 세션 시작 시점과 프롬프트 처리 중에 프레임 편향을 방지합니다.

## 작동 방식

better-research는 두 개의 훅을 등록합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시 한 번 | 무조건 반-프레임-편향 XML 블록 주입 (Layer 1a) |
| `UserPromptSubmit` | Claude가 메시지를 처리하기 전 | 두 가지 경로: 키워드 트리거 디바이어싱 (Layer 1b), 마커 트리거 리서치 프로토콜 (Layer 2) |

### Layer 1a — 세션 수준 반-프레임-편향

세션 시작 시 프롬프트와 무관하게 한 번 주입됩니다. 모든 응답에 앞서 프레이밍을 보류하고, 대안을 열거하고, 가정을 검증하도록 Claude를 준비시킵니다.

### Layer 1b — 키워드 트리거 인지 디바이어싱

프롬프트에 설계 또는 브레인스토밍 키워드가 포함되면 `<cognitive-debiasing>` 블록이 자동으로 주입됩니다:

- **한국어:** 설계, 방법, 접근법, 구현, 어떻게, 전략
- **영어:** design, approach, architect, implement, strategy

마커 없이도 자동으로 감지됩니다.

### Layer 2 — 마커 트리거 리서치 프로토콜

**트리거 마커:** `/q`, `/query`, `/research` — 대소문자 구분 없음, 프롬프트 어느 위치든 가능.

```
/q React에서 상태가 바뀌지 않았는데 왜 리렌더링이 발생하나요?
/research PostgreSQL에서 커넥션 풀이 고갈되는 원인은 무엇인가요?
/query 낙관적 잠금과 비관적 잠금의 차이점은 무엇인가요?
```

마커는 Claude가 질문을 보기 전에 제거됩니다. Claude는 6단계 프로토콜을 실행합니다:

- **Step 0 — 확장적 프레이밍** — 질문을 넓게 재표현하고 3가지 이상의 대안 해석 나열
- **Step 1 — 초기 가설** — 초안 답변, 결론이 아님
- **Step 2 — 출처 검증** — 2개 이상의 독립적인 출처 (공식 문서, 명세서, 소스 코드 우선); 출처가 2개 미만인 주장은 `[UNVERIFIED]` 표시
- **Step 3 — 반론 확인** — 답변이 성립하지 않는 최소 1가지 제한 조건 또는 상황
- **Step 4 — 근본 원인 분석** — 재귀적 "왜" 체인 (최소 3단계); 근본 원인이 파악되기 전까지 해결책 제시 금지
- **Step 5 — 최종 답변** — 결론 → 근거 → 제한 사항 → 출처

## 설치

```
/plugin marketplace add nwleedev/better-research
```

또는 전체 engine 마켓플레이스를 설치합니다:

```
/plugin marketplace add nwleedev/engine
```

## 사용법

질문 앞에 `/q`, `/query`, `/research`를 붙입니다:

```
/q 동시성과 병렬성의 차이는 무엇인가요?
/research Dockerfile 캐시가 매 빌드마다 깨지는 이유는 무엇인가요?
/query 세션 저장소로 Redis와 Memcached 중 어떤 것이 더 좋은가요?
```

마커 없이는 Claude가 평소대로 답변합니다 (단, Layer 1a와 Layer 1b는 여전히 적용됩니다). 마커를 붙이면 Claude는 6단계를 모두 거친 후 최종 답변을 제시합니다.

## 설정

| 변수 | 기본값 | 설명 |
|---|---|---|
| `RESEARCH_PERSPECTIVES` | _(비어 있음)_ | 모든 리서치 요청에 주입할 관점의 쉼표 구분 목록 |

`RESEARCH_PERSPECTIVES`가 설정되면 Claude는 `/q` 마커 없이도 모든 응답에서 나열된 관점을 고려합니다. 모든 응답에 다각도 분석을 강제하려면 이 설정을 사용하세요.

예시 `.env`:

```
RESEARCH_PERSPECTIVES=security,performance,maintainability
```

이 설정이 적용되면 모든 Claude 응답은 보안, 성능, 유지보수성 측면을 고려합니다.
