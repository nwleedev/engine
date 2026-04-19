# harness-engineer

도메인별 코딩 표준을 모든 Claude Code 작업 턴에 주입하고 세션 종료 시 위반 사항을 감지합니다. 이상적인 패턴을 한 번만 정의하면 Claude가 자동으로 준수합니다.

## 작동 방식

harness-engineer는 네 가지 훅을 실행하고 세 가지 명령어를 제공합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시마다 | `.claude/harness/`의 모든 하네스 파일을 컨텍스트로 로드 |
| `UserPromptSubmit` | 각 사용자 메시지 전 | 작업 전에 하네스 패턴을 확인하도록 Claude에 알림 |
| `PreToolUse` | 각 도구 호출 전 | 파일 작성 또는 편집 전에 하네스 준수 여부 강제 |
| `Stop` | 세션 종료 시마다 | 이번 세션에서 수행된 작업을 스캔하고 위반 사항을 `.claude/harness/violations.log`에 기록 |

하네스 파일은 `.claude/harness/`에 저장됩니다:

```
.claude/harness/
├── <domain>.md        # 기술 스택 또는 도메인의 코딩 표준
└── violations.log     # 세션마다 추가됨; /update-harness에서 사용
```

각 하네스 파일에는 파일 패턴, 키워드, 핵심 규칙(체크리스트), `<Good>`/`<Bad>` 코드 예시, 안티패턴 게이트(자기 점검 질문)가 포함됩니다.

## 설치

```
/plugin marketplace add nwleedev/harness-engineer
```

또는 전체 engine 마켓플레이스를 설치합니다:

```
/plugin marketplace add nwleedev/engine
```

## 사용법

### /create-harness

```
/create-harness <기술 스택 설명>
```

예시:

```
/create-harness Next.js 14 App Router + TanStack Query + Tailwind CSS
/create-harness FastAPI + SQLAlchemy + PostgreSQL
/create-harness React Native + Expo + Zustand
```

플러그인이 공식 문서를 가져와 모범 사례를 추출하고 `.claude/harness/<domain>.md`에 하네스 파일을 작성합니다. 생성 후 `file_patterns` 목록을 보여줍니다 — 프로젝트 구조가 다르면 직접 조정하세요.

### /update-harness

```
/update-harness
/update-harness <domain>
```

`violations.log`에서 반복 위반 사항(3회 이상)을 읽고 하네스 `## Anti-Pattern Gate`에 추가할 것을 제안합니다. `<Good>`/`<Bad>` 예시가 없는 규칙도 보완합니다. 각 변경 전에 확인을 요청합니다.

### /evaluate-harness

```
/evaluate-harness
/evaluate-harness <domain>
```

하네스를 5가지 기준으로 평가합니다 (각 10점 만점):

| 기준 | 만점 조건 |
|---|---|
| 패턴 예시 구체성 | 모든 규칙에 `<Good>`/`<Bad>` 코드 예시 있음 |
| 안티패턴 커버리지 | 모든 `violations.log` 항목이 게이트에 포함됨 |
| 파일 길이 | 500줄 미만 |
| 위반 반영 여부 | 반복 위반 중 게이트에 누락된 항목 없음 |
| 최신성 | 30일 이내에 업데이트됨 |

## 설정

| 변수 | 기본값 | 설명 |
|---|---|---|
| `HARNESS_LANGUAGE` | `auto` | 생성되는 하네스 내용의 언어. `auto`는 현재 대화 언어를 따르고, `ko` 또는 `en`은 특정 언어를 강제 |

예시 `.env`:

```
HARNESS_LANGUAGE=en
```
