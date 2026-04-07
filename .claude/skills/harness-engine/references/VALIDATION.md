# Validation

## 목적

`harness-engine`로 만든 하네스가 실제 작업 전에 참고 가능한 상태인지 검증한다.

## 최소 체크리스트

- `task_type` 판정 이유를 설명할 수 있다.
- 이번 실행이 `project-harness generation`인지 `engine-asset bootstrap`인지 설명할 수 있다.
- 공통 `research` phase를 적용했는지 설명할 수 있다.
- 최종 산출물이 `.claude/skills/harness-<domain>-<name>.md`에 있다.
- 목적, 흐름, 금지 패턴, 완료 기준이 분리되어 있다.
- 기존 하네스가 있었다면 왜 보강만 했는지 또는 왜 새 하네스를 만들었는지 설명할 수 있다.
- 기존 하네스가 있었다면 최소 계약 충족 여부를 먼저 판정했고, 미달 시 왜 재사용하지 않았는지 설명할 수 있다.
- 세션 재개 시 어떤 문서를 먼저 읽어야 하는지 드러난다.
- 새 `task_type`를 만들었다면 `.claude/skills/use-repo-skills.md`가 있는 경우 도메인 하네스 목록에 등록되어 있다.
- 최종 문서들에 출처와 설계 근거가 직접 들어 있다.
- 대표 분류 집합으로 처리했는지, 예외적 새 `task_type`인지 설명할 수 있다.
- discovery 등록 형식이 현재 `AGENTS.md`(없으면 `CLAUDE.md`)의 텍스트 포맷과 어긋나지 않는다.
- project contract packet 경로와 revision 상태를 설명할 수 있다.
- contract packet의 필수 작업 축과 금지 패턴이 산출물에 반영되어 있다.
- 현재 저장소 전용 예시/경로/검증 이력이 코어 규칙과 분리되어 있다.
- 핵심 규칙에 도메인 권장 패턴 대비 현재 프로젝트의 보충 분석이 포함되어 있다 (의도적 선택/미충족/해당없음 분류). 소프트웨어 도메인은 아키텍처 패턴, 비소프트웨어 도메인은 방법론/프레임워크를 평가 대상으로 한다.
- 핵심 규칙이 공식 문서 기반이고, 프로젝트 코드가 유일한 근거인 규칙이 없다.
- 프로젝트 전용 사항이 기본 규칙과 구분된 보충 항목으로 기재되어 있다.
- 구조/방법론 평가에서 발견된 미충족 격차가 ANTI_PATTERNS.md와 VALIDATION.md에 반영되어 있다.
- stack이 감지된 경우 stack required checks가 contract packet에 기록되어 있다.
- stack이 감지된 경우 stack-specific 규칙이 산출물의 구조/안티패턴/검증에 반영되어 있다.
- 소프트웨어 도메인이고 스택이 감지된 경우, ANTI_PATTERNS.md의 자동 검출 가능한 안티패턴이 `enforcement/LINT_RULES.md`에 매핑되어 있다.
- `engine_followup_required` 판정이 적절하고 설명 가능하다.
- validation artifact의 저장 위치와 최소 형식을 설명할 수 있다.
- Source Coverage Manifest가 contract packet에 존재하며 UNASSIGNED가 0개이다.
- 생성된 하네스 파일 목록이 Manifest의 대상 하네스 열과 일치한다.
- cross-cutting으로 표시된 소스가 실제로 해당 하네스들에 반영되었다.
- cross-cutting 배포 로그가 세션 notes에 존재한다 (cross-cutting 소스가 있는 경우).

## 검증 서브에이전트

하네스 생성 서브에이전트 완료 후, 독립 인스턴스인 검증 서브에이전트가 이 문서의 기준으로 검증을 수행한다.

### 검증 서브에이전트의 역할

- 하네스 생성 과정을 모르는 독립 인스턴스로서, 생성된 하네스 문서와 contract packet만 읽고 검증한다.
- 자기 검증 편향(verification bias)을 방지하기 위해 하네스를 만든 에이전트와 분리된다.
- worktree에서 생성된 파일은 worktree_path를 통해 접근한다.

### 검증 절차

1. 생성된 `.claude/skills/harness-<domain>-<name>.md` 파일을 읽는다.
2. 공통 `research` phase, task adapter, project contract packet을 함께 읽는다.
3. 선택형 example pack과 stack seed reference가 제공되었다면 추가로 읽는다.
4. 아래 "질문" 항목에 대해 하네스와 관련 reference만으로 답할 수 있는지 확인한다.
5. contract packet 연동 검증 항목을 확인한다.
6. 가상 작업을 시도하고, 하네스에서 빠진 정보를 파악한다.
7. 결과를 보고 형식으로 반환한다.

### 보고 형식

```text
- 누락 항목: [목록]
- 모호 지점: [목록]
- 충돌 규칙: [목록]
- 체크리스트 통과 여부: [항목별]
- engine follow-up required: [yes/no]
- 종합 판정: [통과/보강 필요]
- 구현 시작 허용: [yes/no]
```

본 에이전트는 위 결과를 세션 validation artifact로 `.claude/sessions/<session_id>/notes/validation/`에 저장해야 한다.

## 드라이런 시나리오

최소 1개 이상 수행한다.

1. 기존 하네스 보강 시나리오
   - 기존 `.claude/skills/harness-<domain>-*`를 읽고 최소 계약 충족 여부를 먼저 판정한 뒤 부족한 섹션만 보강
2. 새 하네스 생성 시나리오
   - 기존 하네스로 커버되지 않는 분야에 대해 문서 묶음 생성

## 질문

- 이 하네스만 읽고 다음 작업 절차를 바로 시작할 수 있는가
- 기존 하네스가 약했더라도 왜 바로 구현하면 안 되는지 하네스만으로 설명할 수 있는가
- 안티패턴과 권장 절차가 충돌하지 않는가
- 검증 규칙이 너무 약하거나 과도하지 않은가
- 세션 압축 이후에도 문서만으로 맥락을 이어갈 수 있는가
- 다른 프로젝트에 복사할 때 무엇을 그대로 가져가고 무엇을 로컬에서 다시 만들어야 하는지 보이는가

## contract packet 연동 검증

contract packet이 로드된 경우 추가로 확인한다.

- contract packet이 존재하는가
- contract packet의 프로젝트 목표와 작업 범위가 하네스 문서에 반영되어 있는가
- thin adapter의 최소 Coverage Contract가 모두 하네스 산출물에 반영되었는가
- contract packet의 필수 축이 모두 하네스 산출물에 반영되었는가
- thin adapter의 Anti/Good 최소 필수 쌍이 ANTI_PATTERNS.md에 모두 쌍으로 존재하는가
- contract packet의 프로젝트별 Anti/Good 필수 쌍이 ANTI_PATTERNS.md에 모두 쌍으로 존재하는가
- thin adapter와 contract packet이 서로 충돌하지 않는가
- 선택형 example pack이 있다면 adapter/packet 계약과 충돌하지 않는가
- 코어 규칙과 project adapter / local evidence가 뒤섞이지 않았는가
- contract packet의 `architecture_pattern_evaluation` 축이 핵심 규칙의 보충 분석에 반영되었는가 (소프트웨어 도메인: 아키텍처 패턴 평가, 비소프트웨어 도메인: 방법론/프레임워크 평가, 의도적 선택 기록)
- stack이 감지된 경우 stack required checks가 핵심 규칙, 안티패턴, 검증 기준에 반영되었는가
- stack seed reference가 없더라도 현재 프로젝트 기준 contract packet이 충분히 닫혀 있는가
- `engine_followup_required`가 적절한가

bootstrap을 사용한 경우 (신규 모드/보충 모드 모두) 추가로 확인한다.

- Role-Goal-Backstory가 구체적으로 정의되었는가 (generic 직책 사용 여부)
- human-in-the-loop 검증이 수행되었는가 (사용자 확인 기록)
- 보수적 기본값을 사용한 항목이 명시되어 있는가
- **보충 모드의 경우**: 기존 어댑터의 방법론(HOW)이 유지되고, 프로젝트 고유 도메인 지식(WHAT)만 보충되었는가

## 실패 신호

- 문서가 있는데 적용 시점이 불명확하다.
- 공통 `research` phase를 거치지 않고 task adapter만 적용했다.
- 기존 하네스가 있으나 최소 계약 미달인데도 재사용 결정이 내려졌다.
- contract packet 없이 하네스를 생성하거나 검증했다.
- 안티패턴만 있고 권장 흐름이 없다.
- 권장 흐름만 있고 검증 기준이 없다.
- 최종 산출물이 `temps/`에만 있다.
- 기존 하네스를 읽지 않고 새 디렉터리를 만들었다.
- 새 `task_type`를 만들었는데 `.claude/skills/use-repo-skills.md`가 있음에도 도메인 하네스 목록을 함께 갱신하지 않았다.
- 최종 문서에서 출처를 생략하고 세션 notes/에만 근거를 남겼다.
- 스킬 파일의 frontmatter(name, description, user-invocable)가 누락되어 있다.
- thin adapter 최소 Coverage Contract 필수 축이 하네스에 누락되어 있다.
- contract packet의 프로젝트 필수 축이 하네스에 누락되어 있다.
- thin adapter 또는 contract packet의 Anti/Good 필수 쌍의 한쪽(Anti만 또는 Good만)이 빠져 있다.
- 선택형 example pack이 adapter/packet 계약과 충돌한다.
- 대표 분류인데 adapter가 없었음에도 `engine-asset bootstrap` 경로를 타지 않았다.
- 핵심 규칙에 공식 기준 대비 프로젝트 보충 분석이 없거나, 현 프로젝트의 현재 상태를 무비판적으로 수용하고 있다.
- "현재 코드가 이렇게 하고 있다"만을 근거로 규칙을 서술하고, 공식 문서 출처가 없다.
- 프로젝트 전용 로컬 패턴이 공식 문서 기반 규칙과 혼재되어 구분 없이 기재되어 있다.
- stack이 감지됐는데 contract packet에 stack required checks가 없거나 산출물에 반영되지 않았다.
- 검증 결과가 `통과`가 아닌데 구현 티켓이 시작되었다.
- validation artifact가 저장되지 않았는데 구현 티켓이 시작되었다.
- 테스트 전략이 구현 후 테스트 정합화로 밀렸는데도 하네스가 차단하지 못했다.
- 현재 저장소 전용 경로나 예시가 portable core의 필수 규칙처럼 남아 있다.
