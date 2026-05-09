# codex-session-memory 세션 메모리

Codex CLI 세션의 진행 상황을 증분 컨텍스트 요약으로 저장하는 세션 메모리
플러그인입니다. Claude용 `plugins/session-memory/`와 시맨틱은 닮았지만
코드는 완전히 독립되어 있습니다.

**검증된 Codex 버전:** 0.128.0

## 설치

```
codex plugin marketplace add /path/to/this/repo
```

Codex를 재시작한 뒤 `/plugins`를 열고 `Engine` marketplace에서
`codex-session-memory`를 설치하거나 활성화합니다.

이 플러그인은 스킬을 먼저 호출하는 사용자 호출 방식으로 동작합니다. Codex 생명주기
훅을 자동으로 설치하지 않습니다.

사용 가능한 스킬:

- `$codex-session-memory:install`
- `$codex-session-memory:checkpoint`
- `$codex-session-memory:resume`
- `$codex-session-memory:status`

## 스킬

Codex는 플러그인에 포함된 스킬을 플러그인 네임스페이스와 함께 표시합니다.
`/plugins`에는 플러그인 자체(`codex-session-memory`)가 보이며, 채팅에서
스킬을 호출할 때는 아래 이름을 사용합니다.

| 스킬 | 동작 | LLM 호출 |
|---|---|---|
| `$codex-session-memory:install` | 스킬 우선 세션 메모리를 위한 AGENTS.md 설정 안내 출력 | 0 |
| `$codex-session-memory:checkpoint` | 컨텍스트 체크포인트 인계 준비 및 검증 | 0 |
| `$codex-session-memory:resume [prefix]` | 이전 세션의 INDEX 목록 표시 또는 로드 | 0 |
| `$codex-session-memory:status` | 대기 중인 턴, 컨텍스트 파일 수, 경로 표시 | 0 |

## 컨텍스트 압축 복구

컨텍스트 압축 복구는 런타임 훅이 아니라 AGENTS.md 지침으로 수행됩니다.
같은 Codex 세션에서 수동 또는 자동 컨텍스트 압축이 발생한 뒤에는 첫 번째
작업으로 현재 세션 접두사와 함께 `$codex-session-memory:resume <prefix>`를
호출해 저장된 인계 내용을 다시 로드해야 합니다.

## 프로젝트 루트 해석 (모노레포 가드)

스크립트가 cwd부터 상위 디렉터리로 올라가며 우선순위대로 루트를 결정합니다.

1. `CODEX_PROJECT_DIR` 환경변수
2. `<ancestor>/.env`의 `CODEX_PROJECT_DIR=...` 선언
3. `git rev-parse --show-toplevel`
4. `AGENTS.md`를 포함한 최상위 조상
5. `.codex/`를 포함한 최상위 조상
6. cwd

해석된 루트가 `git rev-parse --show-toplevel`과 다르고 환경변수로 명시한 재정의가 없으면 플러그인은 **쓰기를 거부**합니다 (조용한 데이터 분산보다 명확한 실패를 우선합니다).

### 모노레포 권장 설정

`<root>/.env`에 추가:

```
CODEX_PROJECT_DIR=/abs/path/to/monorepo/root
```

`.env`가 `.gitignore`에 등록됐는지 변경 커밋 전 확인합니다.

## 데이터 레이아웃

```
<root>/.codex/sessions/<CODEX_THREAD_ID>/
├── INDEX.md
└── contexts/CONTEXT-YYYYMMDD-HH00-checkpoint.md

<root>/.codex/sessions/_children/<CHILD_CODEX_THREAD_ID>/
├── INDEX.md
└── contexts/CONTEXT-YYYYMMDD-HH00-checkpoint.md
```

같은 JSONL transcript인 `~/.codex/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl`을
각 체크포인트마다 증분으로 읽습니다.

서브에이전트/리뷰 세션은 자식 세션으로 체크포인트를 만들면 `_children` 아래
저장됩니다. 일반적으로는 아래 명령을 실행합니다.

```
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py prepare --role child
```

자동 부모 확인이 부모를 찾지 못하거나 명시적으로 재정의해야 할 때만
`--parent`를 사용합니다.

```
python3 /path/to/codex-session-memory/skills/checkpoint/checkpoint.py prepare --role child --parent <parent-session-id>
```

자식 `INDEX.md`에는 `role: child`와 `parent_session_id`를 기록하고, 부모
`INDEX.md`에는 `Child Sessions` 항목으로 자식 세션 링크를 추가합니다.
기본 세션 목록은 `_children`을 숨겨 메인 세션 중심으로 표시합니다.

## 자식 세션 체크포인트

전체 부모 결정 순서는 다음과 같습니다.

1. `--parent <thread-id>`
2. `CODEX_SESSION_PARENT_ID`
3. 자동 감지기

자동 감지 안에서는 도우미가 상태 DB보다 rollout `session_meta`를 먼저 읽습니다.
rollout 메타데이터가 자식 세션을 식별하지만 부모 id를 포함하지 않으면, 도우미는
상태 DB가 추측하도록 넘기지 않고 실패로 중단합니다. 상태 DB 대체 조회는 rollout
메타데이터가 없거나 자식 세션으로 식별하지 않는 경우에만 사용합니다. 상태 DB 대체
조회는 `thread_spawn_edges`를 먼저 확인한 뒤 `threads.source`를 확인합니다.

자식 증거가 감지되었지만 부모 id를 확인할 수 없으면, 도우미는 최상위 기본 세션
대상을 출력하지 않고 종료 코드 2로 종료합니다.

`INDEX.md`는 추가 전용 이벤트 로그로 취급합니다. 같은 HH00 context 파일을 여러
번 갱신하더라도 기존 INDEX 라인을 교체하지 말고 새 라인을 추가합니다. resume은
INDEX 이벤트 순서를 보존하되 실제 context 파일 주입은 filename 기준으로 중복 제거해
같은 파일을 여러 번 읽지 않습니다.

## 세션 연속성

`CODEX_THREAD_ID`는 재개된 Codex CLI 세션 사이에서도 동일 유지 — 실측 확인됨. 같은 Codex 세션의 며칠 작업이 동일한 `<root>/.codex/sessions/<id>/INDEX.md`에 누적됩니다.

## 테스트

```
python -m pytest tests/codex-session-memory -q
```
