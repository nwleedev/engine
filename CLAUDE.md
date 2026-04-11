# Project Rules

MUST 규칙은 훅이 기계적으로 강제한다. 이 파일에는 판단이 필요한 규칙만 기술한다.
코드/커밋/파일명: 영어 | 사용자 소통: 한국어

## Research (MUST)

- 출처 우선순위: 공식 문서 > 표준 문서 > 소스 코드 > 블로그. 블로그 단독 근거 금지
- context7 MCP로 라이브러리 문서 참조
- 고영향 주장(기술 선택, 아키텍처 결정)은 독립 근거 2개 이상 확보. 미충족 시 `미확정` 표시
- 반대 근거/제한사항을 최소 1건 확인. 한 방향 근거만으로 결론 금지
- 심층 조사 필요 시: project-researcher 에이전트 위임 또는 /research-methodology 스킬 참조
- 병렬 검색은 턴당 3-4건 제한

## Before Writing Code

- 파일 편집 전 Read, 편집 후 재확인. 같은 파일 3회 이상 연속 편집 시 중간 확인 읽기
- 10턴 이상 또는 컨텍스트 압축 후에는 편집 대상 파일을 반드시 다시 읽는다
- harness 스킬 관련 파일: 해당 harness 스킬 먼저 호출 (훅이 제안)
- 새 작업 시작 시 기존 플랜에 섹션 추가 또는 새 플랜 파일 생성

## Editing

- 주석은 비자명한 WHY만
- 이름 변경 시 모든 참조 범주 검색 (import, type, string, re-export, test, barrel)

## List

**각 리스트는 가능하면 2~7개 항목으로 유지하고, 각 항목은 단독으로 읽어도 의미가 통하도록 작성하며 조건, 근거, 예외를 필요한 범위에서 포함한다.**

## Ambiguity

- 성공 기준 불명확, 범위 변경, 새 의존성, 파괴적 변경: 선택지 제시 후 대기
- 탐색 우선: 질문 전에 코드/설정/테스트/git log 먼저 탐색. 아티팩트로 해결 가능하면 질문 불필요
- 턴당 질문 1개만. 구현 방향을 가장 크게 바꾸는 질문 선택, 구체적 선택지 제시
- 외부 의존성(라이브러리, 도구) 도입 시: 선택지와 장단점을 제시하고 대기

## Verification (MUST)

- 완료 전 검증: 테스트 실행, 출력 확인
- 실패한 검사 억제 금지. 미완료 작업 완료 보고 금지
- 도구 결과가 의심스럽게 적으면 범위를 좁혀 재실행. 절삭이 의심되면 명시

## Collaboration

- 요청이 오해에 기반하거나, 요청 범위 근처에 버그를 발견하면 말한다
- 요청된 것만 구현한다. 관련 개선은 현재 작업 완료 후 별도 제안

## Output Style

- 첫 도구 호출 전에 무엇을 하려는지 간단히 말한다
- 핵심 발견/방향 전환 시 짧은 업데이트. 테이블은 짧은 열거 사실에만 사용

## Failure Response

- 근본 원인 먼저 식별. 테스트 비활성화, 기능 제거, 요구사항 변경 금지

## Turn Summary (SHOULD)

파일 편집이 있는 작업 턴 종료 전, `.claude/sessions/<session_id>/.turn-summary`에 구조화 요약 작성 (덮어쓰기).
포맷: `## Outcome` (1-2문장), `## Decisions` (이유 포함), `## Next steps`, `## Blockers`.
Stop 훅이 이 파일을 컨텍스트 스냅샷에 반영한다. 미작성 시 transcript에서 자동 추출 (폴백).

<!-- HARNESS-SYNC-CORE-END -->
<!-- HARNESS-SYNC-PROJECT-START -->

## Git Commits (MUST)

- .gitignore 등록 파일 커밋 금지. 민감정보(.env, 토큰) 편집/출력 금지
- **작업 턴 종료 시 반드시 변경 사항을 적절하게 분할하여 커밋**. 커밋 누락은 Stop 훅이 감지하여 다음 세션에 경고한다

형식 (Conventional Commits + Angular + 50/72 규칙):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**제목** — `<type>(<scope>): <subject>`:

- type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`
- scope: 선택. 변경 대상 모듈/컴포넌트
- subject: 소문자 시작, 명령형 현재 시제 ("add" not "added"), 끝에 마침표 없음
- 50자 목표, 72자 한도
- 검증: "If applied, this commit will \_\_\_" 문장에 subject를 넣어 자연스러운지 확인

**본문** — WHY 중심:

- 제목과 빈 줄로 분리. 72자 줄바꿈
- **왜** 변경했는가를 설명. 무엇을 했는가는 diff가 보여준다
- 단순 변경(오타, 의존성 업데이트)은 생략 가능

**푸터** — 필요 시:

- `BREAKING CHANGE:` 하위 호환 깨지는 변경 시 필수
- `Fixes #N` 또는 `Closes #N`: 이슈 참조
- `Co-Authored-By:` 공동 작성자

## Enforced by Hooks (참고, 규칙 아님)

- 플랜 없이 코딩 시작 불가 (PreToolUse Write|Edit)
- 2-4개 파일 수정: work-reviewer 단일 검토 알림 (PostToolUse Write|Edit)
- 5+개 파일 또는 인프라 변경: multi-review (2명 병렬) 알림 (PostToolUse Write|Edit)
- 대규모 플랜(4+ 변경 단위) 자동 분할 권고 (plan-readiness-checker 10단계)
- 세션 스냅샷 자동 생성 (Stop hook)
- 미커밋 변경 감지 경고 (Stop hook)
- 컨텍스트 압축 시 SESSION.md + 최신 context + 플랜 경로 재주입 (SessionStart compact)
- ExitPlanMode 첫 호출 시 플랜 재검토 강제 (PreToolUse ExitPlanMode)
- 파괴적 git 명령 차단: --no-verify, --force/-f (push), reset --hard, clean -f, branch -D, checkout -- . (permissions.deny)

## 임시 파일

`temps/<date>/<scope>/` 폴더 내 적절한 위치에 저장한다.

- date: 날짜 ('yyyy-MM-dd')
- scope: 작업의 범위

## Github CLI

- api.github.com HTTP 호출 대신 gh cli 사용을 우선 검토
