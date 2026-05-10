# engine

engine은 Codex와 Claude Code를 위한 멀티 하네스 플러그인 모노레포입니다.

이 저장소는 플러그인 원본, 공유 도메인 로직, 하네스별 렌더러, 생성된
플러그인 산출물을 분리합니다. 현재 생성 산출물은 추적되는 원본에서
재현 가능하며, 사용자가 바로 확인하거나 설치할 수 있도록 커밋됩니다.

## 저장소 구조

| 경로 | 역할 |
|---|---|
| `plugin-sources/` | 마켓플레이스 메타데이터, adapter tree, shared skill, shared subagent, harness-foundry 자료의 표준 원본입니다. |
| `packages/` | 빌드와 검증 도구가 공유하는 런타임 비종속 Python 도메인 로직입니다. |
| `renderers/` | 표준 원본을 Codex와 Claude Code 플러그인 레이아웃으로 변환하는 하네스 렌더러입니다. |
| `plugins/codex/<plugin>` | 생성된 Codex 플러그인 산출물입니다. |
| `plugins/claude/<plugin>` | 생성된 Claude Code 플러그인 산출물입니다. |

동등한 원본 파일이 `plugin-sources/` 또는 `packages/` 아래에 있는 경우
생성된 플러그인 산출물을 직접 수정하지 마세요. 해당 원본, `packages/`의
공유 로직, 또는 `renderers/`의 하네스 출력 규칙을 수정한 뒤 산출물을 다시
생성해야 합니다.

## 플러그인 패밀리

핵심 플러그인 패밀리는 `session-memory`와 `quality-guard`입니다.

현재 생성되는 멀티 하네스 패밀리에는 `session-memory`, `quality-guard`,
`shared-skills`, `shared-subagents`, `harness-foundry`가 있습니다.
`tools/build_plugins.py`는 `plugin-sources/marketplace.yaml`에서
마켓플레이스 메타데이터를 읽고, 그 메타데이터로 Codex와 Claude Code
manifest를 렌더링하며, `plugin-sources/`의 전체 플러그인 트리를 렌더링하고,
`packages/`의 공유 package 코드를 각 runtime artifact의 `_packages/`
디렉터리로 materialize합니다.

## `plugin-sources/`를 사용하는 이유

이 저장소는 최상위 `src/` 대신 `plugin-sources/`를 사용합니다. 표준 입력이
하나의 애플리케이션 런타임 코드가 아니라 플러그인 manifest, skill, agent,
문서, 메타데이터이기 때문입니다. 명시적인 이름을 사용하면 원본 경계가
분명해지고, 표준 플러그인 자료를 생성된 플러그인 패키지나 Python 구현
코드와 혼동하지 않을 수 있습니다.

## 빌드와 검증

저장소 루트에서 다음 플러그인 빌드와 검증 워크플로를 실행합니다:

```bash
python tools/build_plugins.py
python tools/validate_generated.py
pytest
git diff --exit-code
test -z "$(git status --porcelain --untracked-files=all)"
```

`validate-generated` GitHub Actions 워크플로도 같은 계약을 따릅니다.
플러그인 산출물을 다시 생성하고, 생성물을 검증하고, 테스트를 실행하고,
`git diff --exit-code`로 tracked drift를 감지하며,
`git status --porcelain --untracked-files=all`로 untracked 생성 파일까지
감지한 뒤 작업 트리가 바뀌면 실패합니다. CI는 `pytest`를 명시적으로
설치하고, 생성된 변경을 자동 커밋하지 않습니다. 기여자는 원본 수정과
다시 생성된 산출물을 함께 커밋해야 합니다.
