# Output Contract

## 목적

`harness-engine` 작업의 최종 산출물과 임시 산출물을 분리하고, `.claude/skills/` 아래에 어떤 스킬 파일을 남겨야 하는지 정의한다.

## 경로 규칙

- 최종 산출물: `.claude/skills/harness-<domain>-<name>.md` (단일 스킬 파일)
- 임시 메모: `.claude/sessions/<session_id>/notes/*`
- project contract packet: `.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md`
- 스킬 자체 보강 지침: `.claude/skills/harness-engine/**`
- 공통 phase 문서: `.claude/skills/harness-engine/references/common/*.md`
- task adapter: `.claude/skills/harness-engine/references/adapters/<task_type>.md`
- 스킬 내부 reference example: `.claude/skills/harness-engine/references/examples/<task_type>/*`
- 스택 seed 지침: `.claude/skills/harness-engine/references/stacks/<stack>.md`
- 새 하네스 스킬 생성 시 `.claude/skills/use-repo-skills.md`가 있으면 도메인 하네스 목록을 갱신

세션이 없는 환경에서는 `temps/contracts/<task_type>-contract.md`를 사용한다.

## 실행 경로 규칙

`harness-engine`의 생성 작업은 아래 둘 중 하나로 분류한다.

1. `project-harness generation`
   - 대상 프로젝트의 `.claude/skills/harness-<domain>-<name>.md`를 생성/보강하는 일반 경로
   - 기존 adapter가 있거나, 비대표 분류/미지 도메인에 대해 로컬 하네스만 우선 세팅할 때 사용
   - 이 경로에서도 contract packet은 필수다
2. `engine-asset bootstrap`
   - 대표 분류에 adapter가 없을 때, 엔진 자산과 대상 프로젝트 하네스를 한 번에 닫는 경로
   - `.claude/skills/harness-<domain>-<name>.md`와 함께 thin adapter, 필요 시 example pack, stack seed doc까지 생성할 수 있다

대표 분류인데 adapter가 없는 경우에는 일반 경로로 처리하지 않는다.

## 이식성 패키징 규칙

하네스 산출물은 가능한 한 아래 3층을 구분한다.

1. `portable core`
   - 다른 프로젝트로 복사해도 유지될 규칙
2. `project adapter`
   - 현재 프로젝트의 경로, 검증 명령, 스택 연결부
3. `local evidence pack`
   - 현재 저장소 전용 샘플, 드라이런, 과거 검증 기록

규칙:

- 현재 저장소의 예시와 검증 이력을 코어 문서의 필수 규칙처럼 적지 않는다.
- 특정 저장소에만 맞는 경로/명령/예시는 adapter나 evidence로 밀어낸다.
- 새 하네스를 만들 때 project adapter나 local evidence가 필요하면 템플릿 또는 안내 섹션으로 분리한다.
- 스킬 내부 reference example은 조사와 문서 구조의 참고 자료로만 사용하고, 최종 산출물의 필수 규칙으로 승격하지 않는다.
- 프로젝트별 세부 stack/library 규칙은 코어 문서보다 contract packet에 먼저 기록한다.

## discovery 등록 형식

- `AGENTS.md`(없으면 `CLAUDE.md`) 등록 시 현재 문서가 사용하는 섹션형 서술 포맷을 따른다.
- 새 하네스가 기존 큰 범주에 자연스럽게 들어가면 해당 범주 아래 참고 문서 목록에 추가한다.
- 기존 큰 범주로 설명되지 않으면 현재 `AGENTS.md`(없으면 `CLAUDE.md`)와 같은 톤의 새 섹션을 추가한다.
- `.claude/skills/use-repo-skills.md`가 있으면 도메인 하네스 목록에 새 하네스를 추가한다. (파일이 없으면 이 단계를 건너뛴다.)

## 최종 산출물 형식

새 하네스는 **단일 `.claude/skills/harness-<domain>-<name>.md` 스킬 파일**로 생성한다.

파일에 포함할 필수 섹션:
- YAML frontmatter (name, description, user-invocable: true, matchPatterns)
- 핵심 규칙 (아키텍처, 작업 흐름)
- 안티패턴 (Anti/Good 쌍)
- 검증 기준 (완료 조건, 체크리스트)

선택적 섹션:
- enforcement 가이드 (lint, 정적 분석 규칙 매핑)
- 조합 패턴 (다른 라이브러리와의 통합)

정식 adapter를 만들거나 크게 보강할 때 추가:

- `references/adapters/<task_type>.md`
- `references/examples/<task_type>/README.md`
- `references/examples/<task_type>/ANTI_GOOD_REFERENCE.md`
- `references/examples/<task_type>/VALIDATION_REFERENCE.md`

## 단일 스킬 파일 내 섹션 역할

하네스 스킬 파일(`.claude/skills/harness-<domain>-<name>.md`)은 단일 파일이며, 내부에 다음 섹션을 포함한다:

- **frontmatter** (필수)
  - name, description, user-invocable: true
  - description은 "Use when..." 형식으로 자동 활성화 트리거 조건을 기술
  - `matchPatterns` (권장): suggest-harness.sh 훅이 파일 읽기 시 자동 제안하기 위한 매칭 규칙
    - `fileGlob`: 파일 경로 필터 정규식 (선택). 매칭하지 않는 파일은 건너뜀
      - 프론트엔드: `"^.*/src/.*\.(ts|tsx)$"`
      - 백엔드 Python: `"^.*/src/.*\.py$"`
      - 테스트: `"^.*\.(test|spec)\.(ts|tsx)$"`
      - FSD 레이어: `"^.*/src/(app|pages|widgets|features|entities|shared)/.*"`
    - `regex`: 파일 내용 매칭 정규식 배열. 하나라도 매칭하면 해당 하네스를 제안
      - 예: `- "useQuery|useMutation|queryClient"`
    - matchPatterns가 없으면 description의 `— ` 뒤 키워드로 폴백 매칭
    - description은 `Use when working with X — keyword1, keyword2` 형식 필수 (폴백 호환)
- **핵심 규칙** (필수)
  - 소프트웨어 도메인: 작업 흐름, 계층, 역할 분리, 설계 근거
  - 비소프트웨어 도메인: 작업 구조, 방법론, 절차 흐름, 설계 근거
  - 현재 프로젝트 구조/방법론 평가 (도메인 권장 패턴 대비 충족/부분충족/미충족 분류)
- **안티패턴** (필수)
  - 피해야 할 패턴과 차단 규칙, 근거 출처
  - 반드시 Anti/Good 쌍으로 작성
- **검증 기준** (필수)
  - 완료 기준, 검증 체크리스트, 검증 근거
- **enforcement 가이드** (선택, 소프트웨어 도메인)
  - 안티패턴 중 자동 검출 가능한 항목의 린트/정적 분석 규칙 매핑
- **조합 패턴** (선택)
  - 다른 라이브러리와의 통합 패턴 (해당 시)

## 최소 섹션 계약

최종 문서 묶음에는 아래 정보가 드러나야 한다.

- 무엇을 위한 하네스인가
- 언제 적용하는가
- 어떤 절차로 진행하는가
- 무엇을 금지하는가
- 무엇을 보면 완료라고 판단하는가
- 세션 재개 시 무엇을 읽으면 되는가
- 출처와 설계 근거가 어디에 있는가
- 프로젝트 전용 연결부가 코어와 어떻게 분리되는가
- contract packet에서 확정한 프로젝트 스택과 검증 포인트가 어떻게 반영되는가
- 프로젝트의 구조/방법론이 도메인 권장 패턴을 어떻게 충족/미충족하는지, 의도적 일탈이 있는지

## Anti/Good 쌍 완성도 규칙

- 어댑터가 정의한 최소 Anti/Good 필수 쌍 목록의 모든 케이스에 대해, ANTI_PATTERNS.md에 Anti와 Good이 **반드시** 존재해야 한다.
- contract packet이 정의한 프로젝트별 Anti/Good 필수 쌍도 모두 존재해야 한다.
- 한쪽(Anti만 또는 Good만)만 있으면 산출물이 불완전한 것으로 판정한다.
- 각 쌍에는 케이스명을 명시하여 Anti와 Good의 대응 관계가 명확해야 한다.

## Example Pack 규칙

- example pack은 선택형 engine-internal reference 자산이다.
- example pack은 adapter의 규범 계약이나 contract packet을 대체하지 않는다.
- example pack이 없어도 생성/검증 경로는 성립해야 한다.
- example pack이 있다면 adapter 또는 contract packet과 충돌하지 않아야 한다.
- example pack은 대상 프로젝트 runtime 문서로 sync하지 않는다.

## Contract Packet 규칙

- 모든 생성/보강/검증 작업은 contract packet을 기준으로 한다.
- contract packet은 세션 산출물이지만, 이번 프로젝트에 대한 생성/검증의 표준 진실원천이다.
- thin adapter는 최소 하한선을 제공하고, contract packet은 실제 프로젝트 stack/library 조합을 닫는다.
- validator는 contract packet 경로, revision, engine follow-up 필요 여부를 artifact에 남겨야 한다.

### Source Coverage Manifest (contract packet 필수 섹션)

contract packet에는 반드시 Source Coverage Manifest를 포함해야 한다. 이 섹션은 모든 소스 자료가 하네스에 빠짐없이 매핑되었는지를 추적한다.

형식:

```markdown
## Source Coverage Manifest

| 소스 파일 | 대상 하네스 | 유형 |
|---|---|---|
| STATE_MANAGEMENT.md | harness-fe-zustand | direct |
| REFACTORING.md | harness-fe-testing, harness-fe-fsd | cross-cutting |
| UX_REVIEW.md | harness-fe-fsd, harness-fe-react-hook-form | cross-cutting |

UNASSIGNED 수: 0
```

규칙:
- 모든 소스 파일은 최소 1개 하네스에 매핑되어야 한다.
- 유형은 `direct` (1:1 매핑) 또는 `cross-cutting` (1:N 매핑)이다.
- `UNASSIGNED` 항목이 1개라도 있으면 생성 서브에이전트 실행을 금지한다 (HARD GATE).
- cross-cutting 소스에는 반드시 Cross-Cutting Distribution 섹션이 동반되어야 한다.

### Cross-Cutting Distribution (contract packet 필수 섹션, cross-cutting 존재 시)

Source Coverage Manifest에 `cross-cutting` 유형이 있으면, 각 cross-cutting 소스에 대해 배포 지시를 작성해야 한다.

형식:

```markdown
## Cross-Cutting Distribution

### REFACTORING.md
- 대상: harness-fe-testing, harness-fe-fsd
- 배포 방식: 리팩토링 안전 체크리스트를 각 하네스의 검증 기준에 추가
- 배포 내용: rename/move 안전 규칙, 참조 무결성 확인 절차

### UX_REVIEW.md
- 대상: harness-fe-fsd, harness-fe-react-hook-form
- 배포 방식: UX 일관성 기준을 검증 기준에 추가
- 배포 내용: 동적 필드 UX 표준, 접근성 체크리스트
```

규칙:
- 각 cross-cutting 소스에 대해 대상, 배포 방식, 배포 내용을 명시한다.
- 생성 서브에이전트는 이 지시에 따라 각 대상 하네스에 내용을 반영한다.
- 반영 후 세션 notes에 배포 로그를 기록한다.

## 예시 코드 규칙

- 예시 코드는 Markdown 코드 블록으로 제시한다.
- 소스 코드 파일을 예시 용도로 직접 생성하지 않는다.
- 예시가 특정 프레임워크나 도구에 묶이면, 그 전제 조건을 함께 적는다.

## 어댑터 연동 규칙

- 모든 하네스 생성은 먼저 공통 `research` phase를 적용한다.
- 하네스 생성 시 해당 도메인 어댑터의 최소 Coverage Contract가 모두 산출물에 반영되어야 한다.
- contract packet의 프로젝트별 필수 작업 축과 금지 패턴이 산출물에 반영되어야 한다.
- 어댑터가 정의한 1차 근거 소스를 산출물의 출처 체계에 반영한다.
- 대표 분류인데 adapter가 없다면 `engine-asset bootstrap` 경로로 전환해 어댑터 파일과 필요 시 example pack, stack seed doc까지 함께 생성한다.
- stack seed reference가 있으면 참고하되, 산출물의 최종 기준은 contract packet으로 고정한다.

## 서브에이전트 산출물 규칙

- `project-harness generation` 경로의 서브에이전트는 `.claude/skills/harness-<domain>-<name>.md` 파일을 생성/수정한다.
- `engine-asset bootstrap` 경로이거나 현재 작업이 harness-engine 자체의 재사용 자산 보강이라면 `references/adapters/<task_type>.md`, `references/examples/<task_type>/*`, `references/stacks/<stack>.md`, `references/common/*.md`도 생성/수정할 수 있다.
- 세션 파일(SESSION.md)은 서브에이전트가 갱신하지 않는다 (본 에이전트 책임).
- `.claude/skills/use-skills.md`는 서브에이전트가 갱신하지 않는다 (본 에이전트 책임).
- worktree 격리 사용 시, 산출물은 worktree 내 `.claude/skills/` 경로에 생성된다.
- 서브에이전트는 완료 시 생성/수정 파일 목록, 실행 경로, Coverage 충족 상태, Anti/Good 쌍 충족 상태, contract packet 사용 상태, engine follow-up 필요 여부, 미충족 항목을 보고한다.

## 환류 패킷 규칙

복사된 프로젝트에서 하네스 변경 요청을 되돌릴 때는 아래 필드가 있어야 한다.

- source project
- copied artifact scope
- failure or friction
- expected behavior
- reproduction task
- local constraint
- proposed generalization
- evidence

재현 정보와 일반화 판단이 없으면 코어 변경 요청으로 승격하지 않는다.

## 실제 프로젝트 보고 템플릿

하네스를 다른 프로젝트에 복사해 사용할 수 있도록, 아래 템플릿을 portable core의 기본 부속물로 유지한다.

보고서는 `.claude/sessions/<session_id>/notes/`에 직접 작성한다.

역할:

- 실제 프로젝트에서 하네스 계층 문제가 발생했을 때 즉시 구조화 리포트를 남긴다.
- contract packet은 프로젝트별 stack/library 계약을 정리하는 임시 진실원천 역할을 한다.
- validation report는 하네스 검증 통과 여부와 구현 시작 허용 여부를 세션 산출물로 남기는 역할을 한다.
- validation artifact에는 이번 실행이 `project-harness generation`인지 `engine-asset bootstrap`인지, `engine_followup_required`가 있는지도 남긴다.

## 범용 에이전트와의 조합 규칙

하네스 스킬은 단독으로 사용되지 않고, 범용 에이전트와 조합하여 도메인별 동작을 수행한다. 하네스 생성 시 도메인별 전용 에이전트를 따로 만들지 않는다.

### 스킬과 에이전트의 역할 분담

- **스킬** = 도메인 지식 (무엇을 알아야 하는가): 핵심 규칙, 안티패턴, 검증 기준
- **에이전트** = 적용 방법 (어떻게 적용하는가): 검토, 학습, 조사 흐름

### 조합 패턴

| 단계 | 에이전트 | 하네스 스킬 활용 |
|---|---|---|
| 사전 학습 | `domain-tutor` | 하네스의 핵심 규칙 → 커리큘럼, 안티패턴 → 학습 자료, 검증 기준 → 완료 기준 |
| 작업 중 | Claude (본 에이전트) | description 매칭 또는 `/harness-*`로 활성화하여 규칙 참조 |
| 작업 후 | `work-reviewer` | 하네스의 안티패턴 → 위반 검증, 검증 기준 → 체크리스트 통과 판정 |

### 하네스 산출물 작성 시 고려

하네스 스킬을 작성할 때, 범용 에이전트가 동적으로 읽어 활용한다는 점을 전제로 한다:
- 안티패턴의 Anti/Good 쌍은 work-reviewer가 위반 여부를 기계적으로 판단할 수 있도록 구체적으로 작성한다.
- 검증 기준의 체크리스트는 항목별 pass/fail 판정이 가능하도록 명확하게 작성한다.
- 핵심 규칙은 domain-tutor가 학습 Unit으로 변환할 수 있도록 독립적인 개념 단위로 구분한다.
