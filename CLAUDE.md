# Project Rules

MUST 규칙은 훅이 기계적으로 강제한다. 이 파일에는 판단이 필요한 규칙만 기술한다.
코드/커밋/파일명: 영어 | 사용자 소통: 한국어

## Research (MUST)

- 출처 우선순위: 공식 문서 > 표준 문서 > 소스 코드 > 블로그. 블로그 단독 근거 금지
- context7 MCP로 라이브러리 문서 참조

## Before Writing Code

- 파일 편집 전 Read, 편집 후 재확인
- harness 스킬 관련 파일: 해당 harness 스킬 먼저 호출 (훅이 제안)
- 새 작업 시작 시 기존 플랜에 섹션 추가 또는 새 플랜 파일 생성

## Editing

- 주석은 비자명한 WHY만
- 이름 변경 시 모든 참조 범주 검색 (import, type, string, re-export, test, barrel)

## Ambiguity

- 성공 기준 불명확, 범위 변경, 새 의존성, 파괴적 변경: 선택지 제시 후 대기

## Verification (MUST)

- 완료 전 검증: 테스트 실행, 출력 확인
- 실패한 검사 억제 금지. 미완료 작업 완료 보고 금지

## Failure Response

- 근본 원인 먼저 식별. 테스트 비활성화, 기능 제거, 요구사항 변경 금지

## Git Commits

- .gitignore 등록 파일 커밋 금지. 민감정보(.env, 토큰) 편집/출력 금지
- 작업 턴 종료 시 커밋. 형식: `<type>(<scope>): <subject>`

<!-- HARNESS-SYNC-CORE-END -->
<!-- HARNESS-SYNC-PROJECT-START -->

## Enforced by Hooks (참고, 규칙 아님)

- 플랜 없이 코딩 시작 불가 (PreToolUse Write|Edit)
- 3개+ 파일 수정 시 work-reviewer 알림 (PostToolUse Write|Edit)
- 세션 스냅샷 자동 생성 (Stop hook)
- 컨텍스트 압축 시 SESSION.md + 최신 context + 플랜 경로 재주입 (SessionStart compact)
- ExitPlanMode 첫 호출 시 플랜 재검토 강제 (PreToolUse ExitPlanMode)
- git commit --no-verify 차단 (permissions.deny)
