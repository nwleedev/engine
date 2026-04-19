# session-memory

자동 세션 컨텍스트 요약 및 주입 플러그인입니다. 매 세션 시작 시 Claude는 최근 3개 세션의 요약을 배경 컨텍스트로 받습니다 — 별도 설정이 필요 없습니다.

## 작동 방식

session-memory는 네 가지 훅을 실행합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시마다 | 최근 3개 세션 요약을 읽고 컨텍스트로 주입 |
| `Stop` | 세션 종료 시마다 | 세션을 요약하고 `.claude/sessions/<id>/INDEX.md`에 기록 |
| `PreToolUse` | 각 도구 호출 전 | 세션 데이터가 실수로 수정되지 않도록 보호 |
| `PreCompact` | 컨텍스트 압축 전 | 현재 컨텍스트를 체크포인트 파일로 요약 |

세션 요약은 `.claude/sessions/<session_id>/`에 저장됩니다:

```
.claude/sessions/<session_id>/
├── INDEX.md          # 세션 요약 (session_id, 타임스탬프 포함 프론트매터)
└── contexts/
    └── CONTEXT-*.md  # 압축 중 생성된 체크포인트 스냅샷
```

가장 최근 세션은 전체 `INDEX.md`와 최대 3개의 컨텍스트 스냅샷을 제공합니다. 이전 세션은 `INDEX.md`만 제공합니다.

## 설치

```
/plugin marketplace add nwleedev/session-memory
```

또는 전체 engine 마켓플레이스를 설치합니다 (4개 플러그인 모두 포함):

```
/plugin marketplace add nwleedev/engine
```

## 사용법

명령어나 트리거 키워드가 없습니다. 플러그인은 완전 자동으로 동작합니다:

1. Claude Code 세션을 열고 평소대로 작업합니다.
2. 세션이 종료되면 Claude가 작업 내용을 요약하고 `INDEX.md`를 작성합니다.
3. 다음 세션 시작 시 Claude는 최근 3개 요약을 배경 컨텍스트로 받습니다.

주입된 컨텍스트는 Claude의 시스템 컨텍스트로 제공됩니다 — 화면에는 표시되지 않지만, Claude는 이전 작업을 참조하는 질문에 답변할 때 이를 활용합니다.
