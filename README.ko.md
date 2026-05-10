# engine

engine은 Codex와 Claude Code를 위한 멀티 하네스 플러그인 모노레포입니다.

이 저장소는 플러그인 원본, 공유 도메인 로직, 하네스별 렌더러, 생성된
플러그인 산출물을 분리합니다. 이 구조는 단계적으로 도입되고 있으며,
현재 생성 산출물을 재현 가능하게 유지하면서 더 많은 플러그인 패밀리를
같은 원본 경계로 옮기는 중입니다.

## 저장소 구조

| 경로 | 역할 |
|---|---|
| `plugin-sources/` | 현재 마켓플레이스 메타데이터와 shared-skills 참조 자료의 표준 원본입니다. |
| `packages/` | 빌드와 검증 도구가 공유하는 런타임 비종속 Python 도메인 로직입니다. |
| `renderers/` | 표준 원본을 Codex와 Claude Code 플러그인 레이아웃으로 변환하는 하네스 렌더러입니다. |
| `plugins/codex/<plugin>` | 생성된 Codex 플러그인 산출물입니다. |
| `plugins/claude/<plugin>` | 생성된 Claude Code 플러그인 산출물입니다. |

동등한 원본 파일이 `plugin-sources/` 아래에 이미 있는 경우 생성된 플러그인
산출물을 직접 수정하지 마세요. 해당 원본, `packages/`의 공유 로직, 또는
`renderers/`의 하네스 출력 규칙을 수정한 뒤 산출물을 다시 생성해야 합니다.
일부 생성 manifest는 전체 플러그인 원본 트리가 이전되기 전에 이미 존재하며,
해당 패밀리는 이후 작업에서 `plugin-sources/`로 옮겨집니다.

## 플러그인 패밀리

핵심 플러그인 패밀리는 `session-memory`와 `quality-guard`입니다.

현재 생성되는 멀티 하네스 패밀리에는 `shared-skills`, `shared-subagents`,
`harness-foundry`가 있습니다. 지금 `tools/build_plugins.py`는
`plugin-sources/marketplace.yaml`에서 마켓플레이스 메타데이터를 읽고,
그 메타데이터로 Codex와 Claude Code manifest를 렌더링하며,
`plugin-sources/shared-skills/`에서 `shared-skills` 트리를 렌더링합니다.
`shared-subagents`, `harness-foundry`, 그리고 다른 플러그인 패밀리 자료의
전체 표준 원본 이전은 이후 작업에서 진행됩니다.

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
```

`validate-generated` GitHub Actions 워크플로도 같은 계약을 따릅니다.
플러그인 산출물을 다시 생성하고, 생성물을 검증하고, 테스트를 실행하고,
`git diff --exit-code`로 drift를 감지한 뒤 작업 트리가 바뀌면 실패합니다.
CI는 생성된 변경을 자동 커밋하지 않습니다. 기여자는 원본 수정과 다시
생성된 산출물을 함께 커밋해야 합니다.
