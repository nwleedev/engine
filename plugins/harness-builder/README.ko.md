# harness-builder

웹 검색과 공식 문서를 활용해 모든 기술 스택에 맞는 품질 하네스를 동적으로 설정하는 플러그인입니다.

## 기능

- `package.json`, `go.mod`, `pyproject.toml` 등의 표준 파일을 읽어 기술 스택 자동 탐지
- 공식 문서에서 최신 베스트 프랙티스 수집 (Tavily + Context7)
- `.claude/harness/<domain>.md` 생성 — 클로드가 작업 시 참조하는 품질 기준
- 린터 설정 파일 생성 (ESLint, Ruff, golangci-lint, Stylelint 등)
- `CLAUDE.md`에 `## Harness Standards` 참조 항목 추가
- 세션 종료 시 변경된 파일에 대한 하네스 검토 자동 실행

## 명령어

| 명령어 | 용도 |
|---|---|
| `/harness-setup` | 초기 설정 — 스택 탐지, 문서 검색, 하네스 및 린터 설정 파일 생성 |
| `/harness-sync` | 기존 하네스를 현재 스택 상태에 맞게 갱신 |
| `/harness-audit` | 특정 파일을 하네스 기준으로 감사 |

## 자동 동작

- **세션 시작**: 하네스 존재 여부를 감지하고 컨텍스트로 주입
- **세션 종료**: 해당 세션에서 변경된 파일 목록과 함께 하네스 검토 요청

## 생성 파일 (사용자 프로젝트)

```
사용자-프로젝트/
  CLAUDE.md                          ← ## Harness Standards 섹션 추가
  .claude/
    harness/
      <domain>.md                    ← 클로드용 품질 기준
  eslint.config.js                   ← 린터 설정 파일 생성
  pyproject.toml                     ← [tool.ruff] 섹션 추가
```

## 커버리지 확장

일반적인 언어는 자동 탐지가 지원됩니다. 미지원 언어(Elixir, Swift 등)의 경우 `/harness-setup` 실행 시 스택을 직접 설명하면 웹 검색 기반으로 하네스를 생성합니다.

언어 자동 탐지를 영구적으로 추가하려면 `plugins/harness-builder/scripts/stack_detector.py`의 `DETECTION_TABLE`에 항목을 추가하는 PR을 열어주세요.
