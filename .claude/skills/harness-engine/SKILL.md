---
name: harness-engine
description: "사용자가 언급한 작업 분야에 맞춰 `.claude/skills/harness-<domain>-<name>.md` 하네스 스킬을 만들거나 보강하는 스킬. 본 에이전트가 판정과 사용자 상호작용을 담당하고, 서브에이전트가 도메인 조사와 하네스 생성을 수행한다."
user-invocable: true
---

# Harness Engine

이 스킬의 목적은 사용자가 언급한 작업 분야에 대해 Claude가 반복적으로 참고할 수 있는 하네스 스킬을 `.claude/skills/harness-<domain>-<name>.md`에 세팅하는 것이다.

본 에이전트는 판정, 사용자 상호작용, 세션 관리를 담당하고, 하네스 생성과 검증은 서브에이전트에 위임한다.

이 스킬은 완전 정적 규칙 엔진도 아니고, 매번 처음부터 다시 조사하는 완전 동적 엔진도 아니다. 기본 구조는 다음과 같다.

- 공통 조사 규율: `references/common/RESEARCH_PHASE.md`
- 얇은 도메인 최소 계약: `references/adapters/<task_type>.md`
- 프로젝트별 진실원천: 세션 경로의 `contract packet`
- 선택형 품질 보강: `references/examples/<task_type>/*`

## 언제 사용하는가

- 새 작업 분야에 대한 하네스가 아직 없을 때
- 기존 `.claude/skills/harness-<domain>-*` 스킬이 너무 약해서 실제 작업 기준으로 쓰기 어려울 때
- 특정 분야에 대해 안티패턴, 아키텍처, 검증 기준, 템플릿을 보강해야 할 때
- 사용자가 "이 분야 작업 전에 Claude가 뭘 참고해야 하는가"를 문서화하려 할 때
- 다른 프로젝트에 portable core만 sync한 뒤, 그 프로젝트 전용 작업 분야 하네스를 처음 만들 때

## 빠른 절차 (본 에이전트)

1. 사용자 요청에서 목적과 작업 분야를 추출한다.
2. 대표 분류 집합에서 후보 `task_type`를 먼저 고른다.
3. 기존 `.claude/skills/harness-<domain>-*` 스킬이 있는지 확인한다.
4. 기존 하네스가 있으면 최소 계약 충족 여부를 먼저 판정한다.
5. 최소 계약 미달이면 기존 하네스를 재사용하지 말고 보강 모드로 전환한다.
6. 이번 작업이 `project-harness generation`인지 `engine-asset bootstrap`인지 먼저 판정한다.
7. 공통 `research` phase를 먼저 수행한다.
8. 도메인 task adapter를 로드하고, 스택/라이브러리 조합을 확인한다.
9. 세션 경로에 프로젝트별 `contract packet`을 만들거나 갱신한다.
10. Coverage 갭 또는 미지 도메인이면 공통 bootstrap phase와 사용자 검증을 수행하고 contract packet을 보강한다.
11. 선택형 example pack과 stack seed reference가 있으면 참고 자료로만 로드한다.
12. **Source Coverage Manifest를 작성하고 검증한다 (HARD GATE).** 모든 소스 파일이 최소 1개 하네스에 매핑되었는지 확인한다. UNASSIGNED가 0이 아니면 사용자에게 매핑 결정을 요청하고 대기한다. cross-cutting 유형이 있으면 Cross-Cutting Distribution도 작성한다.
13. **하네스 생성 서브에이전트를 실행한다.**
14. **검증 서브에이전트를 실행한다.**
15. 검증 결과를 contract packet에 먼저 반영한 뒤 하네스를 보강한다.
16. 새 하네스 스킬을 만들었다면 `.claude/skills/use-repo-skills.md`의 도메인 하네스 목록을 갱신한다. (use-repo-skills.md가 없으면 생성한다.)
17. 세션 기록(SESSION.md)을 갱신한다.

## 작업 시작 전 확인

- 루트 `AGENTS.md`, `.claude/skills/core-rules.md`를 읽었는지 확인한다.
- 특히 임시 파일 규칙(temps 경로, `/tmp` 금지)을 확인한다.
- `CLAUDE.md`의 프로젝트별 설정을 확인한다.
- 사용자 요청만으로 범위가 닫히는지 확인한다.
- 최종 산출물이 어떤 스킬 파일명(`harness-<domain>-<name>.md`)이 될지 결정한다.
- 프로젝트 전용 예시나 검증 이력을 코어 문서에 넣을지 여부를 먼저 검토하지 않는다. 먼저 `portable core` / `project adapter` / `local evidence pack` 분리 원칙을 적용한다.
- 이미 있는 하네스가 있다면 우선 읽고, 덮어쓰지 말고 보강 방향을 잡는다.
- 다른 프로젝트에서 core만 sync한 상태라면, 이 스킬이 해당 프로젝트의 첫 로컬 작업 분야 하네스를 만드는 공식 경로임을 전제로 한다.
- 사용자가 해당 도메인에 익숙하지 않다고 명시했다면, `learning-mode`를 병행 적용할지 먼저 판정한다.
- 모든 실행은 `references/common/RESEARCH_PHASE.md`를 먼저 적용한다.
- 최소 계약의 진실원천은 `common + thin adapter + contract packet`이다.
- `references/examples/<task_type>/`는 참고용 evidence로만 읽고, portable core 규칙처럼 복사하지 않는다.
- 기존 하네스가 있더라도 아래 최소 계약을 충족하지 못하면 `재사용 가능`으로 판정하지 않는다.
  - 핵심 규칙, 안티패턴, 검증 기준 섹션 존재
  - 작업 분야에 맞는 직접 예시 코드 또는 직접 사례 존재
  - 출처와 설계 근거 직접 포함
  - 세션 재개 순서와 구현 시작 전 체크리스트 존재

## 작업 분야 Intake

`references/TASK_INTAKE.md`를 읽고 아래를 먼저 판정한다.

- 어떤 `task_type`인지
- 기존 하네스를 재사용하는지
- 새 하네스를 만들어야 하는지
- 어떤 문서 묶음이 필요한지
- contract packet이 필요한 스택/라이브러리 조합이 무엇인지

대표 분류 집합을 기본값으로 먼저 검토한다.

실질적인 후보가 2개 이상이면 자동 확정하지 말고 사용자에게 선택지를 제시하고 대기한다.

## 공통 research phase + thin adapter + project contract packet

`task_type` 판정 후, 기존 하네스의 품질을 먼저 판정하고 공통 `research` phase를 수행한 뒤 해당 도메인의 thin adapter를 로드한다.

### 기존 하네스 품질 판정

기존 `.claude/skills/harness-<domain>-*` 스킬이 있으면 아래를 먼저 확인한다.

- 핵심 규칙, 안티패턴, 검증 기준 섹션이 모두 존재하는가
- 작업 분야에 맞는 직접 예시 코드 또는 직접 사례가 있는가
- 출처와 설계 근거가 문서 내부에 직접 있는가
- 세션 재개 순서와 구현 시작 전 체크리스트가 보이는가

위 항목 중 하나라도 아니면, 기존 하네스는 `존재하지만 재사용 불가`로 판정하고 보강 모드로 전환한다.

### 공통 research phase

모든 `task_type`는 먼저 `references/common/RESEARCH_PHASE.md`를 적용한다.

이 단계에서 최소한 다음을 닫는다.

- 1차 근거 소스 우선순위
- 최신성 확인
- 실패 모드 또는 제한 사항
- Anti/Good 직접 사례 후보
- 검색 실행 안전 규칙

`research`가 최종 `task_type`이어도 이 phase를 먼저 수행하고, 그 다음 `references/adapters/research.md`를 추가 적용한다.

### 어댑터가 있는 경우

`references/adapters/<task_type>.md`가 존재하면 로드한다.

어댑터는 최소 계약만 제공한다. 프로젝트별 스택/라이브러리/품질 기준은 세션 경로의 contract packet에 기록한다.

선택형 example pack이 있으면 확인한다.

- `README.md`
- `ANTI_GOOD_REFERENCE.md`
- `VALIDATION_REFERENCE.md`

위 3개는 hard gate가 아니라 reference-only evidence다. 다만 존재한다면 adapter 계약과 충돌하지 않는지 본다.

### project contract packet 작성

모든 생성/보강 작업은 세션 경로에 프로젝트별 contract packet을 만든 뒤 진행한다.

- 기본 경로: `.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md`
- 세션이 없으면: `temps/contracts/<task_type>-contract.md`

contract packet에는 최소한 다음이 있어야 한다.

- 프로젝트 목표와 작업 범위
- 실제 프레임워크/라이브러리/런타임 스택
- 필수 작업 축
- 금지 패턴
- stack-specific required checks
- 공식 문서 출처 목록
- 보수적 기본값과 미확정 항목
- engine follow-up 필요 여부

### Coverage 갭 체크

다음 중 **2개 이상** 해당하면 bootstrap 보충을 실행한다.

- 이 프로젝트의 1차 근거 소스를 즉시 3개 이상 나열할 수 없다
- 이 프로젝트의 핵심 지표/메트릭을 즉시 정의할 수 없다
- 어댑터의 Coverage Contract 필수 축에서 이 프로젝트에 적합한 항목이 절반 미만이다
- 사용자가 해당 프로젝트의 도메인에 대한 지식이 부족하다고 명시했다

### bootstrap 보충 (Coverage 갭 감지 시)

`references/common/BOOTSTRAP_PHASE.md`를 **보충 모드**로 실행한다. 본 에이전트가 사용자 검증(human-in-the-loop)을 수행하고, 확정된 Coverage Contract를 contract packet에 반영한다.

### 공식 MCP 권장안 (선택)

- Tavily MCP: 최신 웹 검색과 원문 추출 보강에 적합하다.
- Context7 MCP: 라이브러리/프레임워크 문서 문맥 보강에 적합하다.
- 둘 다 선택형 도구이며, 최종 규칙과 인용은 공식 문서 또는 실제 소스 코드로 다시 확인한다.

### 어댑터가 없는 경우

1. **대표 분류 집합에 해당하지만 어댑터가 아직 없는 경우**: 일반 하네스 생성으로 보내지 않는다. 실행 경로를 `engine-asset bootstrap`으로 전환하고 thin adapter, contract packet, 필요한 stack seed 자산까지 함께 닫는다.
2. **미지 도메인인 경우**: `references/common/BOOTSTRAP_PHASE.md`를 신규 모드로 실행한다. 본 에이전트가 Role-Goal-Backstory 정의와 사용자 검증을 수행한 뒤, 확정된 내용을 contract packet과 `project-harness generation` 경로의 입력으로 전달한다. 대표 분류 승격은 별도 결정이 없으면 하지 않는다.

### 스택 분기 (해당 시)

어댑터에 스택 분기 섹션이 있으면 `references/stacks/<stack>.md`를 확인한다.

- 스택 감지 순서: 프로젝트 AGENTS.md/CLAUDE.md 선언 → 설정 파일 확인 → 사용자에게 선택 요청
- stack seed reference는 조사 보조 자료다. 생성/검증의 최종 진실원천은 contract packet이다.
- stack doc가 없고 실행 경로가 `engine-asset bootstrap`이면 seed doc까지 같은 턴에 생성한다.
- stack doc가 없고 실행 경로가 `project-harness generation`이면 현재 프로젝트 하네스와 contract packet에는 필요한 규칙을 반영하고, engine 자산 부재를 `engine_followup_required: yes`로 남긴다.

## 이식성 판정

하네스를 만들거나 보강하기 전에, 추가할 내용을 아래 셋 중 어디에 두어야 하는지 먼저 판정한다.

1. `portable core`
   - 다른 프로젝트에도 그대로 유지될 규칙
   - 진입점, 작업 흐름, 금지 패턴, 완료 기준
2. `project adapter`
   - 경로, 검증 명령, 로컬 정책, 프로젝트 스택 같은 연결 지점
3. `local evidence pack`
   - 현재 저장소 전용 드라이런, 샘플, 과거 실패 기록

규칙:

- 현재 저장소의 예시, 절대경로, 기존 실패 이력은 기본적으로 `local evidence pack` 후보로 본다.
- 특정 프로젝트의 연결부는 코어로 올리지 말고 adapter 성격의 문서나 템플릿으로 민다.
- 다른 프로젝트에서 하네스를 복사해 쓴 뒤 생긴 문제를 되돌릴 때는 원본 하네스 저장소에 change request packet을 제출한다.
- 실제 프로젝트에서 하네스 계층 문제를 만나면 `.claude/sessions/<session_id>/notes/`에 이슈 보고서를 작성한다.

## 하네스 생성 서브에이전트 실행

사용자 상호작용이 완료되고 모든 결정 사항이 확정되면, 하네스 생성 서브에이전트를 실행한다.

### 실행 설정

```text
Agent tool 호출:
  description: "harness generation for {domain}"
  subagent_type: general-purpose
  isolation: worktree
  run_in_background: false (포그라운드)
  prompt: (아래 프롬프트 구성 참조)
```

커스텀 에이전트 `.claude/agents/harness-researcher/`가 존재하면 Claude Code가 description 매칭으로 자동 위임할 수 있다. 자동 위임이 안 되면 위 general-purpose 설정을 사용한다.

### 서브에이전트에 전달할 프롬프트 구성

```text
다음 파일을 읽고 하네스 산출물을 생성해주세요.

1. 생성 지침: .claude/skills/harness-engine/references/GENERATION.md
2. 산출물 규칙: .claude/skills/harness-engine/references/OUTPUT_CONTRACT.md

주의: 임시 파일은 반드시 session_path 아래 notes/에 기록합니다. /tmp 사용 금지.

작업 정보:
- task_type: {task_type}
- execution_path: {project-harness generation | engine-asset bootstrap}
- common_research_path: {.claude/skills/harness-engine/references/common/RESEARCH_PHASE.md}
- adapter_path: {adapter_path 또는 "없음"}
- contract_packet_path: {.claude/sessions/<session_id>/notes/contracts/<task_type>-contract.md 또는 temps/contracts/...}
- example_pack_path: {references/examples/<task_type>/ 또는 "없음"}
- bootstrap_phase_path: {공통 bootstrap phase 경로 또는 "해당 없음"}
- bootstrap_mode: {new/supplement/none}
- coverage_contract: {coverage_contract 내용}
- user_decisions: {사용자 확정 사항}
- existing_harness_path: {기존 하네스 경로 또는 "없음"}
- session_path: {세션 디렉터리 경로}
- stack: {스택 정보 또는 "해당 없음"}
- stack_reference_path: {references/stacks/<stack>.md 또는 "없음"}
- stack_required_checks: {contract packet에 반영한 stack required checks}
- engine_followup_required: {yes/no}
- coverage_manifest: {contract packet 내 Source Coverage Manifest 내용}
- cross_cutting_distribution: {contract packet 내 Cross-Cutting Distribution 내용 또는 "없음"}
```

### 서브에이전트 결과 처리

서브에이전트가 반환하는 정보:

- 생성/수정된 파일 목록
- 조사 근거 요약
- Coverage 충족 상태
- Anti/Good 쌍 충족 상태
- contract packet 사용 상태
- 선택형 example pack 사용 상태
- stack 반영 상태
- `engine_followup_required`
- 미충족 항목
- worktree_path (worktree 격리 사용 시)

결과를 확인하고, 미충족 항목이 있으면 사용자에게 보고한 뒤 대응을 결정한다.
`통과`가 아니면 구현 티켓을 시작하지 않는다.

## 검증 서브에이전트 실행

하네스 생성 서브에이전트가 완료되면, 검증 서브에이전트를 실행한다.

### 실행 설정

```text
Agent tool 호출:
  description: "harness validation for {domain}"
  subagent_type: general-purpose
  isolation: 없음 (worktree 미사용 — 읽기만 수행)
  run_in_background: false (포그라운드)
  prompt: (아래 검증 프롬프트 참조)
```

### 검증 서브에이전트 프롬프트

```text
다음 경로의 하네스 문서만 읽고 검증을 수행해주세요.

하네스 경로: {worktree_path}/.claude/skills/harness-{domain}-{name}.md
검증 기준: .claude/skills/harness-engine/references/VALIDATION.md
임시 파일 규칙: session_path 아래 temps/에만 기록. /tmp 사용 금지.
공통 research phase: {.claude/skills/harness-engine/references/common/RESEARCH_PHASE.md}
task adapter: {adapter_path 또는 "없음"}
project contract packet: {contract_packet_path}
example pack: {example_pack_path 또는 "없음"}
bootstrap phase: {bootstrap_phase_path 또는 "해당 없음"}
execution path: {project-harness generation | engine-asset bootstrap}
stack seed reference: {stack_reference_path 또는 "없음"}

검증 방법:
1. 하네스 문서와 관련 engine reference만 읽고, 다음 가상 작업을 수행해보세요: {가상 작업 시나리오}
2. 하네스에서 빠진 정보, 모호한 지시, 충돌하는 규칙을 보고해주세요.
3. VALIDATION.md의 최소 체크리스트와 contract packet 충족 여부, stack-specific 체크를 항목별로 통과 여부 판정해주세요.

보고 형식:
- 누락 항목: [목록]
- 모호 지점: [목록]
- 충돌 규칙: [목록]
- 체크리스트 통과 여부: [항목별]
- engine follow-up required: [yes/no]
- 종합 판정: [통과/보강 필요]
- 구현 시작 허용: [yes/no]
```

### 검증 결과 처리

- **통과**: worktree 유지. 사용자에게 결과 보고. discovery 등록(AGENTS.md, INDEX.md) 필요 시 수행. 본 에이전트는 validation artifact를 세션 경로에 저장한 뒤에만 구현 티켓을 시작한다.
- **보강 필요**: 검증 보고의 누락/모호/충돌 항목을 contract packet에 먼저 반영한 뒤 하네스 생성 서브에이전트에 전달하여 재실행한다. 구현은 금지한다.

## 세션 관리 (본 에이전트 책임)

서브에이전트는 세션 파일을 갱신하지 않는다. 본 에이전트가 다음을 담당한다.

- SESSION.md: 작업 상태, 결정 사항, 진행 로그 갱신
- contract packet: `.claude/sessions/<session_id>/notes/contracts/` 또는 `temps/contracts/`에 저장
- validation artifact: `.claude/sessions/<session_id>/notes/validation/` 또는 `temps/validation/`에 저장
- `.claude/skills/use-repo-skills.md`: 새 하네스 스킬 생성 시 도메인 하네스 목록 갱신
- 다른 프로젝트 환류 요청이 있으면 change request packet의 핵심 필드를 DECISIONS 또는 RESEARCH에 남긴다.
- 실제 프로젝트에서 수집한 보고서가 있으면 원문 전체 대신 핵심 필드만 추려 upstream 판단 자료로 사용한다.
- stack이 감지된 작업이었다면 `engine_followup_required`와 stack required checks가 validation artifact에 남는지 확인한다.

## 기존 하네스 재사용 원칙

- 이미 현재 프로젝트에 충분한 `.claude/skills/harness-<domain>-*` 스킬이 있으면 새 스킬을 만들지 않는다.
- “충분한 하네스”는 최소 계약과 검증 통과를 모두 만족하는 경우만 의미한다.
- 부족한 섹션만 보강한다.
- 새 하네스는 기존 하네스로는 반복적으로 커버되지 않는 경우에만 만든다.
- 새 하네스를 만들었다면 discovery를 위해 `.claude/skills/use-repo-skills.md`의 도메인 하네스 목록 갱신까지 완료해야 한다.
- 기존 하네스를 보강할 때도 portable core와 local evidence를 섞지 않는다.

## 금지

- `task_type` 판단 없이 바로 새 디렉터리 생성
- 최종 산출물을 `temps/`에만 남기고 종료
- 서브에이전트에 사용자 확정 전의 미결 사항을 전달하기
- 검증 서브에이전트를 생략하기
- 최소 계약 미달 기존 하네스를 그대로 재사용하기
- contract packet 없이 하네스 생성/검증을 진행하기
- 대표 분류인데 adapter가 없는 상태를 일반 하네스 생성으로 처리하기
- stack이 감지됐는데 contract packet에 stack required checks를 남기지 않기
- 검증 결과가 `통과`가 아닌데 구현 티켓을 시작하기
- Anti/Good 쌍의 한쪽만 작성하고 완료로 처리하기
- 최종 문서에 출처를 남기지 않고 세션 notes에만 근거를 두기
- 현재 저장소 전용 예시를 portable core 규칙으로 승격하기
- 복사형 사용 중 생긴 문제를 재현 정보 없이 코어 변경 요청으로 올리기

## 참고 파일

- Intake 기준: `references/TASK_INTAKE.md`
- 생성 지침 (서브에이전트용): `references/GENERATION.md`
- 산출물 기준: `references/OUTPUT_CONTRACT.md`
- 검증 기준: `references/VALIDATION.md`
- 공통 조사 phase: `references/common/RESEARCH_PHASE.md`
- 도메인 어댑터: `references/adapters/<task_type>.md`
- 공통 bootstrap phase: `references/common/BOOTSTRAP_PHASE.md`
- 스택 seed 지침: `references/stacks/<stack>.md`
- example pack: `references/examples/<task_type>/*`
- contract packet은 `.claude/sessions/<session_id>/notes/contracts/`에 직접 작성한다.
- 커스텀 리서치 에이전트: `.claude/agents/harness-researcher/AGENT.md`
