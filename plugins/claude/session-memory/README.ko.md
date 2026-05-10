# session-memory

세션 단위 컨텍스트 요약 및 명시적·격리된 재개를 제공하는 플러그인입니다. 각 Claude Code 세션은 작업 중 자체 `INDEX.md`를 작성하고, 사용자가 직접 어느 세션을 재개할지 선택합니다 — 세션 간 자동 혼합이 없습니다.

## 작동 방식

session-memory는 네 가지 훅을 실행합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시마다 | source 기반 분기: `startup`은 `INSIGHT.md`(프로젝트 전반 하이라이트)만 주입, `resume`은 해당 세션의 `INDEX.md` 재주입, `compact`는 최근 컨텍스트 재주입, `clear`는 주입 없음. 8KB 한도. |
| `Stop` | 매 턴 종료 시 | 내레이션 게이트: 트랜스크립트 변동 ≥1KB, 60KB 하드캡 미초과, 마지막 내레이션 이후 ≥300초일 때만 실행. Haiku 4.5 강제, 연속 3회 실패 시 폴백. |
| `PreToolUse` | 각 도구 호출 전 | 동일 게이트로 턴 중간 체크포인트를 생성해 긴 턴에서도 내레이션이 누락되지 않게 함. |
| `SessionEnd` | 세션 종료 시 | 임계값과 무관하게 마지막 내레이션을 강제 실행. |

v1의 `PreCompact`, `UserPromptSubmit`은 제거되었습니다 — `PreCompact`는 macOS 버그와 `additionalContext` 미지원 문제가 있었고, `SessionStart`의 `source="compact"`가 압축 후 인계를 대체합니다.

### 격리

각 `session_id`는 완전히 격리됩니다. `SessionStart`의 `startup`은 다른 세션의 컨텍스트를 자동 주입하지 **않으므로**, 동일 프로젝트에서 병렬로 실행되는 터미널끼리 상태가 섞이지 않습니다. `find_project_root`는 git 최상위를 우선하기 때문에 모노레포 하위 패키지가 별도의 `.claude/sessions/`를 만들 수 없습니다.

### 저장 구조

```
.claude/sessions/
├── INSIGHT.md                       # 프로젝트 전반 하이라이트 (최대 200개)
├── INSIGHT-archive-<YYYY-MM>.md     # 롤오프된 항목
├── _archive/<YYYY-MM>/<id>.tar.gz   # 30일 초과 세션
└── <session_id>/
    ├── INDEX.md                     # 프론트매터 포함 세션 요약
    ├── log.jsonl                    # 결정별 진단 로그
    └── contexts/
        └── CONTEXT-*.md             # 세션 중간 체크포인트 스냅샷
```

30일 초과 세션은 `_archive/<YYYY-MM>/`로 tar.gz 압축됩니다. `INSIGHT.md`는 200개 한도이며, 초과 시 오래된 50개가 `INSIGHT-archive-<YYYY-MM>.md`로 이동합니다.

## 슬래시 명령

| 명령 | 용도 |
|---|---|
| `/session-memory:resume` | 현재 프로젝트의 세션 목록 메뉴; 선택한 세션의 `INDEX.md`만 주입 |
| `/session-memory:status` | 현재 세션 통계와 `log.jsonl`의 최근 결정 출력 |
| `/session-memory:checkpoint` | 게이트 임계값과 무관하게 즉시 내레이션 강제 실행 |
| `/session-memory:migrate` | v1 `INDEX.md` 항목 중복 제거; `--dry-run` 및 `--apply` 지원 |

## 설치

```
/plugin marketplace add nwleedev/session-memory
```

또는 전체 engine 마켓플레이스를 설치합니다 (4개 플러그인 모두 포함):

```
/plugin marketplace add nwleedev/engine
```

## 사용법

훅은 자동 실행되며 트리거 키워드가 없습니다.

1. 세션을 열고 평소대로 작업합니다. `Stop`/`PreToolUse`가 주기적으로 `INDEX.md`와 `contexts/`에 진행 상황을 기록합니다.
2. 이전 세션을 이어서 작업하려면 `/session-memory:resume`을 실행해 메뉴에서 선택합니다 — 선택한 세션의 컨텍스트만 주입됩니다.
3. 위험한 작업 전 강제 내레이션이 필요하면 `/session-memory:checkpoint`를 실행합니다.
4. 게이트의 결정을 점검하려면 `/session-memory:status`를 실행합니다.

주입된 컨텍스트는 Claude의 시스템 컨텍스트로 들어갑니다 — 화면에 표시되지 않지만, 이전 작업을 참조하는 대화에서 Claude가 활용합니다.

## 진단

모든 내레이션 결정(허용·생략·사유)은 `.claude/sessions/<session_id>/log.jsonl`에 기록됩니다. `/session-memory:status`가 이 로그를 읽습니다. 내레이션이 너무 적거나 잦다면 어느 게이트(델타·하드캡·시간 간격·실패 카운트 폴백)가 작동하는지 이 로그로 확인할 수 있습니다.

## v1에서 마이그레이션

기존 session-memory v1의 `.claude/sessions/<id>/INDEX.md`가 있다면 다음을 실행하세요:

```
/session-memory:migrate --dry-run
/session-memory:migrate --apply
```

레거시 항목 중복을 제거해 v2 SessionStart 주입 예산(8KB)을 유지합니다.
