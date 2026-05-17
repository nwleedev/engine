# session-memory 세션 메모리

Codex CLI 세션의 진행 상황을 증분 컨텍스트 요약으로 저장하는 세션 메모리
플러그인입니다. Claude artifact인 `plugins/claude/session-memory/`와 시맨틱은 닮았지만
코드는 완전히 독립되어 있습니다.

**검증된 Codex 버전:** 0.129.0

## 설치

```
codex plugin marketplace add /path/to/this/repo
```

Codex를 재시작한 뒤 `/plugins`를 열고 `Engine` marketplace에서
`session-memory`를 설치하거나 활성화합니다.

이 플러그인은 스킬을 먼저 호출하는 사용자 호출 방식으로 동작합니다. Codex 생명주기
훅을 자동으로 설치하지 않습니다.

사용 가능한 스킬:

- `$session-memory:install`
- `$session-memory:checkpoint`
- `$session-memory:resume`
- `$session-memory:status`

## 스킬

Codex는 플러그인에 포함된 스킬을 플러그인 네임스페이스와 함께 표시합니다.
`/plugins`에는 플러그인 자체(`session-memory`)가 보이며, 채팅에서
스킬을 호출할 때는 아래 이름을 사용합니다.

| 스킬                              | 동작                                                  | LLM 호출 |
| --------------------------------- | ----------------------------------------------------- | -------- |
| `$session-memory:install`         | 스킬 우선 세션 메모리를 위한 AGENTS.md 설정 안내 출력 | 0        |
| `$session-memory:checkpoint`      | 컨텍스트 체크포인트 인계 준비 및 검증                 | 0        |
| `$session-memory:resume [prefix]` | 이전 세션의 INDEX 목록 표시 또는 로드                 | 0        |
| `$session-memory:status`          | 대기 중인 턴, 컨텍스트 파일 수, 경로 표시             | 0        |

## 컨텍스트 압축 복구

컨텍스트 압축 복구는 런타임 훅이 아니라 AGENTS.md 지침으로 수행됩니다.
같은 Codex 세션에서 수동 또는 자동 컨텍스트 압축이 발생한 뒤에는 첫 번째
작업으로 현재 세션 접두사와 함께 `$session-memory:resume <prefix>`를
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
<root>/.codex/session-memory/threads/<CODEX_SESSION_ID>/
├── INDEX.md
└── contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md
```

같은 JSONL transcript인 `~/.codex/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl`을
각 체크포인트마다 증분으로 읽습니다.

`CODEX_THREAD_ID`는 이 transcript lookup에만 사용합니다. 새 체크포인트
artifact는 아래 경로에만 기록됩니다.

```
.codex/session-memory/threads/<CODEX_SESSION_ID>/
```

Codex를 시작하거나 resume하기 전에 `CODEX_SESSION_ID`를 메인 세션 id로
설정합니다. 커밋될 수 있는 `.env`보다 inline env 실행을 권장합니다.

```
CODEX_SESSION_ID=<main-thread-id> codex resume <main-thread-id>
```

Flat `INDEX.md` frontmatter에는 `session_id`, `last_processed_offset`,
`source_thread_id`, `last_updated` 같은 체크포인트 메타데이터를 기록합니다.
`role` 또는 `parent_session_id`는 관계의 source-of-truth 필드로 기록하지
않습니다. `CODEX_THREAD_ID`와 `CODEX_SESSION_ID`가 다르면 checkpoint는
논블로킹 경고를 출력하고 계속 `CODEX_SESSION_ID` artifact에 기록합니다. 잘못된
`CODEX_SESSION_ID`는 다른 세션 artifact를 오염시킬 수 있으므로 명시적 저장
대상으로 취급해야 합니다.

기존 `.codex/sessions/<thread>/contexts`와
`.codex/sessions/_children/<thread>/contexts` 파일은 호환성을 위해 계속 읽을 수
있습니다. `_children`는 deprecated 상태이며, 새 체크포인트가 만들지 않습니다.
지원되는 용도는 legacy 읽기 호환성뿐입니다.

## Artifact-only mode

Flat artifact는 영속적인 복구 단위입니다. session-memory는 checkpoint, resume,
status에서 Codex sqlite state DB, `thread_spawn_edges`, `threads.source`,
rollout `session_meta`, 부모/자식 graph helper를 읽지 않습니다. Artifact-only
mode에서는 다음처럼 동작합니다.

- `$session-memory:status`는 현재 `CODEX_SESSION_ID` artifact만 보고합니다.
- `$session-memory:resume <prefix>`는 선택한
  `.codex/session-memory/threads/<id>/INDEX.md`와 최근 `contexts/` 중심으로
  작업을 재개합니다.
- 체크포인트 CONTEXT는 호환성 섹션으로 `graph_context`를 유지하지만, graph와
  parent discovery를 사용하지 않았다고 기록합니다.
- context 파일을 쓴 뒤 `INDEX.md` update가 실패하면 context는 보존하고, helper는
  context path, 가능한 경우 backup path, 수동 repair 지침을 출력합니다.

이 모델은 작업 맥락 보존량을 줄이는 변경이 아닙니다. 필수 9-section CONTEXT
template는 `executive_summary`, `detailed_state`, `next_actions`,
`graph_context`와 나머지 인계 섹션을 함께 보존해, 압축 복구 시 간결한 상태와
구체적인 작업 맥락을 모두 다시 읽을 수 있게 합니다.

## 병렬 체크포인트

Context 파일은 `contexts/CONTEXT-<timestamp>-<task-id>-<nonce>.md` 형식으로
생성합니다. `source_thread_id`는 파일명이 아니라 context metadata에 기록합니다.
`INDEX.md` 업데이트는 `INDEX.md.lock`을 잡고, lock 안에서 최신 파일을 다시 읽고,
같은 디렉터리에 writer별 backup/temp 파일을 만든 뒤 temp 파일 fsync와
`os.replace`로 최종 교체합니다.

## 세션 연속성

`CODEX_SESSION_ID`는 session-memory의 명시적 artifact id입니다. 같은
`CODEX_SESSION_ID`를 계속 전달할 때에만 같은 Codex 세션의 며칠 작업이 동일한
`<root>/.codex/session-memory/threads/<id>/INDEX.md`에 누적됩니다.

## 기존 자식 세션 마이그레이션

마이그레이션 도우미는 아직 `.codex/sessions` 아래 남아 있는 legacy session-memory
artifact에 사용합니다. 대상은 legacy main session, 최상위 child session,
그리고 legacy `.codex/sessions/_children/<id>` child session입니다.

먼저 dry-run으로 이동 계획을 확인합니다.

```bash
python3 plugins/codex/session-memory/scripts/migrate_child_sessions.py --root /path/to/project
```

계획을 검토한 뒤 실제 적용합니다.

```bash
python3 plugins/codex/session-memory/scripts/migrate_child_sessions.py --root /path/to/project --apply
```

도우미는 각 source를 `.codex/session-memory/threads/<id>/`로 이동하고,
destination conflict와 duplicate destination을 사전 검사하며, destination
`INDEX.md`에서 `role`, `parent_session_id` 같은 relationship frontmatter를
제거합니다. legacy parent INDEX에서 `_children`로 향하는 synthetic link를 찾으면
깨진 링크를 제거하지만 새 `Child Sessions` 링크는 추가하지 않습니다. 적용 중
실패하면 가능한 범위에서 롤백합니다. 파일 복구까지 실패하면 수동 정리 진단을
출력합니다.

## 개발

Canonical source는 repository source tree에 있습니다. Generated plugin artifact는
runtime session-memory plugin directory에 있습니다. Canonical README, skill,
script 파일을 바꾼 뒤에는 다음 명령을 실행합니다.

```bash
rtk python tools/build_plugins.py
rtk python tools/validate_generated.py
```

## 테스트

```
python -m pytest tests/codex-session-memory -q
```
