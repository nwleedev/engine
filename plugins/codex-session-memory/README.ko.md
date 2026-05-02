# codex-session-memory

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

수동 스킬은 설치 후 바로 사용할 수 있습니다. 자동 모드를 사용하려면 아래
Codex hooks 기능 플래그가 필요합니다.

## 자동 모드

Codex 설정에서 Codex hooks를 활성화합니다:

```toml
[features]
codex_hooks = true
```

이 플러그인은 `SessionStart`로 압축 컨텍스트를 주입하고, `Stop`으로 정책
가드를 통과한 자동 체크포인트를 저장합니다. `PostToolUse`는 stop hook이
체크포인트 필요 여부를 판단할 때 사용할 evidence를 표시합니다. 수동 스킬은
계속 사용할 수 있습니다:

- `$codex-session-memory:checkpoint`
- `$codex-session-memory:resume`
- `$codex-session-memory:status`

## 스킬

Codex는 플러그인에 포함된 스킬을 플러그인 네임스페이스와 함께 표시합니다.
`/plugins`에는 플러그인 자체(`codex-session-memory`)가 보이며, 채팅에서
스킬을 호출할 때는 아래 이름을 사용합니다.

| 스킬 | 동작 | LLM 호출 |
|---|---|---|
| `$codex-session-memory:checkpoint` | delta 턴을 컨텍스트 요약으로 저장 | 1 (codex-exec, ~15-60초) |
| `$codex-session-memory:resume [prefix]` | 이전 세션의 INDEX 목록 표시 또는 로드 | 0 |
| `$codex-session-memory:status` | pending 턴, 컨텍스트 파일 수, 경로 표시 | 0 |

## 프로젝트 루트 해석 (모노레포 가드)

스크립트가 cwd부터 walk-up하며 우선순위대로 root 결정:

1. `CODEX_PROJECT_DIR` env var
2. `<ancestor>/.env`의 `CODEX_PROJECT_DIR=...` 선언
3. `AGENTS.md`를 포함한 topmost 조상
4. `.codex/`를 포함한 topmost 조상
5. `git rev-parse --show-toplevel`
6. cwd

해석된 root가 `git rev-parse --show-toplevel`과 다르고 env 명시 override가 없으면 플러그인은 **쓰기를 거부**합니다 (silent 데이터 분산보다 loud failure 우선).

### 모노레포 권장 설정

`<root>/.env`에 추가:

```
CODEX_PROJECT_DIR=/abs/path/to/monorepo/root
```

`.env`가 `.gitignore`에 등록됐는지 변경 commit 전 확인.

## 데이터 레이아웃

```
<root>/.codex/sessions/<CODEX_THREAD_ID>/
├── INDEX.md
└── contexts/CONTEXT-YYYYMMDD-HHMM-<title>.md
```

## 세션 연속성

`CODEX_THREAD_ID`는 `codex exec resume <id>` 사이에서도 동일 유지 — 실측 확인됨. 같은 Codex 세션의 며칠 작업이 동일한 `<root>/.codex/sessions/<id>/INDEX.md`에 누적됩니다.

## 테스트

```
python -m pytest tests/codex-session-memory -q
```
