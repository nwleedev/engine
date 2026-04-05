# Generation (하네스 생성 서브에이전트 지침)

## 목적

이 문서는 harness-engine의 하네스 생성 서브에이전트가 읽는 실행 지침이다. 본 에이전트(조율 담당)가 서브에이전트를 실행할 때 이 파일 경로를 전달하고, 서브에이전트는 이 문서를 읽고 하네스 산출물을 생성한다.

## 서브에이전트가 받는 입력

본 에이전트로부터 다음 정보를 전달받는다.

- `task_type`: 판정된 작업 분야
- `execution_path`: `project-harness generation` 또는 `engine-asset bootstrap`
- `common_research_path`: 공통 조사 phase 문서 경로
- `adapter_path`: 어댑터 파일 경로 (또는 "없음")
- `contract_packet_path`: 프로젝트별 contract packet 경로
- `example_pack_path`: 선택형 example pack 경로 (또는 "없음")
- `bootstrap_phase_path`: 공통 bootstrap phase 문서 경로 (또는 "해당 없음")
- `bootstrap_mode`: `new`, `supplement`, `none`
- `coverage_contract`: 사용자 확정된 Coverage Contract (필수 축 + 조건부 축)
- `user_decisions`: 사용자가 확정한 선택 사항 (bootstrap 검증 결과 포함)
- `existing_harness_path`: 기존 하네스가 있으면 해당 경로 (보강 모드 시)
- `session_path`: 세션 디렉터리 경로
- `stack`: 스택 정보 (또는 "해당 없음")
- `stack_reference_path`: stack seed reference 문서 경로 (또는 "없음")
- `stack_required_checks`: contract packet에 기록된 stack required checks
- `engine_followup_required`: `yes` 또는 `no`
- `coverage_manifest`: Source Coverage Manifest (소스 파일 → 대상 하네스 매핑 테이블)
- `cross_cutting_distribution`: Cross-Cutting Distribution 지시 (또는 "없음")

## 실행 절차

### 1. 공통 research phase 로드

전달받은 `common_research_path`를 먼저 읽고, 다음을 파악한다.

- 1차 근거 소스 우선순위
- 최신성 확인 원칙
- 검색 실행 안전 규칙
- 반대 근거 또는 실패 모드 수집 원칙

이 단계는 모든 `task_type`에서 공통으로 적용한다.

### 2. thin adapter 로드

전달받은 `adapter_path`의 어댑터를 읽고, 다음 항목을 파악한다.

- Coverage Contract의 최소 필수 축
- 1차 근거 소스
- Anti/Good 최소 필수 쌍
- 최소 드라이런 기준

대표 분류에 adapter가 없어서 `execution_path`가 `engine-asset bootstrap`인 경우에는, 본 에이전트가 전달한 `coverage_contract`와 `user_decisions`를 어댑터 초안의 기준으로 사용한다.

### 2.5. Source Coverage Manifest 및 Cross-Cutting Distribution 확인

전달받은 `coverage_manifest`를 읽고 다음을 확인한다:
- 현재 생성할 하네스가 manifest의 대상 하네스에 포함되어 있는지
- cross-cutting 소스가 있으면 `cross_cutting_distribution`의 배포 지시를 확인한다
- 배포 지시에 따라 cross-cutting 내용을 해당 하네스의 적절한 섹션에 반영할 준비를 한다

반영 대상: 핵심 규칙, 안티패턴, 검증 기준 중 배포 지시에서 지정한 섹션.

### 3. project contract packet 로드

`contract_packet_path`를 읽고, 이 문서를 이번 프로젝트의 생성 기준점으로 사용한다.

규칙:

- contract packet이 생성/검증의 최종 진실원천이다.
- adapter보다 packet의 프로젝트별 stack/library 규칙을 우선한다.
- packet에 미확정 항목이 있으면 문서에 그대로 드러나게 하고, 하네스가 그 미확정성을 숨기지 않게 한다.

### 4. 기존 하네스 확인

`existing_harness_path`가 있으면 기존 하네스를 읽고, 부족한 섹션을 파악한다. 덮어쓰지 않고 보강 방향을 잡는다.

### 5. 선택형 example pack 확인

`example_pack_path`가 있으면 필요한 파일만 읽는다.

규칙:

- 이 경로는 정답 복사본이 아니라 reference-only evidence다.
- 예시의 문체나 구조를 참고할 수는 있지만, 프로젝트 스택과 무관한 내용을 그대로 복사하지 않는다.
- 현재 저장소 전용 사례는 portable core가 아니라 예시로만 취급한다.
- example pack이 없어도 생성 자체는 진행한다.
- example pack이 있다면 adapter나 contract packet과 충돌하는 내용을 final harness에 넣지 않는다.

### 6. stack seed reference 확인

`stack_reference_path`가 있으면 해당 문서를 읽고, `stack_required_checks`와 대조한다.

규칙:

- stack seed reference는 조사 보조 자료다.
- stack이 감지된 경우 실제 반영 기준은 contract packet이다.
- seed doc가 없는데 `execution_path`가 `engine-asset bootstrap`이면 필요한 seed doc까지 함께 생성할 수 있다.
- seed doc가 없는데 `execution_path`가 `project-harness generation`이면, 현재 대상 프로젝트 하네스에는 필요한 규칙을 반영하고 `engine_followup_required`를 유지한다.

### 7. 이식성 패키징 판정

추가하려는 내용을 아래 셋 중 어디에 둘지 먼저 판정한다.

- `portable core`: 다른 프로젝트에도 유지될 규칙
- `project adapter`: 프로젝트별 경로, 검증 명령, 스택 연결부
- `local evidence pack`: 현재 저장소 전용 드라이런, 샘플, 검증 기록

규칙:

- 현재 저장소의 예시, 절대경로, 과거 실패 이력을 코어 규칙으로 쓰지 않는다.
- 코어 문서에 로컬 연결부가 꼭 필요하면 템플릿 또는 “프로젝트에서 채워야 하는 항목” 형태로만 남긴다.

### 8. 도메인 조사

공통 research phase와 어댑터의 1차 근거 소스 규칙을 함께 적용해 조사를 수행한다. 어댑터에 1차 근거 소스가 정의되어 있지 않으면 공통 research phase의 범용 순서를 따른다.

1. 해당 도메인의 공식 문서 (프레임워크, 라이브러리, 표준 기관 등)
2. 표준 문서 (RFC, W3C, ISO 등)
3. 실제 오픈소스 코드/문서
4. 공개 이슈나 보조 자료

블로그 단독 근거로 하네스 규칙을 확정하지 않는다.

가능하다면 다음 선택형 MCP를 보조 도구로 사용할 수 있다.

- Tavily MCP: 최신 웹 검색과 원문 추출 보강
- Context7 MCP: 라이브러리/프레임워크 문서 문맥 보강

단, MCP 결과는 공식 문서나 실제 소스 코드로 다시 확인한다.

#### 검색 실행 안전 규칙

- 단일 턴에서 병렬 검색 호출은 최대 3~4건으로 제한한다.
- 5건 이상 필요하면 배치를 나누어 실행한다.
- 각 검색의 max_results는 3~5건으로 제한한다.
- 검색 결과 중 무관한 대용량 항목(PDF, 코드 파일, vocab 파일 등)은 즉시 제외한다.
- 각 배치 완료 후 핵심 발견을 세션 notes(`<session_path>/notes/`)에 기록한 뒤 다음 배치를 진행한다.
- 검색 대상 언어/지역이 다른 경우 언어별로 배치를 분리한다.

#### 도메인 탐색 서브에이전트 실행 (선택)

다음 중 2개 이상 해당하면 내부적으로 도메인 탐색 서브에이전트를 실행한다.

- 이 프로젝트의 1차 근거 소스를 즉시 3개 이상 나열할 수 없다
- 이 프로젝트의 핵심 지표/메트릭을 즉시 정의할 수 없다
- 어댑터의 Coverage Contract 필수 축에서 이 프로젝트에 적합한 항목이 절반 미만이다

도메인 탐색 서브에이전트 실행 시:

- subagent_type: general-purpose
- 지시: "[도메인]에 대해 핵심 작업 축(최소 6개), 실패 모드(최소 5개), 권위 있는 1차 근거 소스, 전문가가 사용하는 품질 기준, Anti/Good 쌍에 쓸 수 있는 구체적 사례를 조사해주세요."
- 출력: Coverage 보충 정보 + 근거 소스 + 사례

### 9. 구조/방법론 평가

도메인 조사 결과를 바탕으로 현재 프로젝트의 구조 또는 방법론을 해당 도메인의 권장 패턴 대비 평가한다.

#### 평가 대상 판정

도메인 유형에 따라 평가 대상을 다르게 잡는다.

- **소프트웨어 도메인** (frontend, backend, ops, security, testing 등): 프로젝트의 소프트웨어 아키텍처를 권장 패턴(Layered, Clean, Hexagonal, FSD 등) 대비 평가한다.
- **조사/분석 도메인** (시장 조사, 경쟁 분석, 사용자 리서치 등): 조사 방법론을 업계 표준 방법론(정량/정성 조사, 삼각검증, 가설-검증 루프 등) 대비 평가한다.
- **전략/설계 도메인** (제품 설계, 수익화 전략, 사업 기획 등): 전략 프레임워크를 검증된 모델(린 캔버스, 비즈니스 모델 캔버스, 디자인 씽킹 등) 대비 평가한다.
- **미지 도메인**: 도메인 조사에서 확인한 해당 분야의 확립된 프레임워크나 방법론이 있으면 그것을 기준으로 평가한다. 확립된 기준이 없으면 contract packet에 "평가 기준 미확정"으로 기록하고, 사용 가능한 근거만으로 보수적 평가를 수행한다.

#### 절차

1. 도메인 조사에서 확인한 권장 패턴/방법론/프레임워크를 정리한다.
   - 공식 문서, 표준, 검증된 프로젝트/사례를 패턴 출처로 사용한다.
   - 어댑터에 스타일 분기가 정의되어 있으면 contract packet에서 확정된 스타일을 평가 기준으로 삼는다.
   - 어댑터가 없으면 (engine-asset bootstrap 경로) 도메인 조사와 contract packet만으로 평가 기준을 수립한다.

2. 현재 프로젝트의 구조/방법론을 각 권장 패턴에 대해 분류한다.
   - 충족 (satisfied): 패턴을 따르고 있음
   - 부분 충족 (partially satisfied): 일부만 따르고 있으며, 구체적 격차를 기록
   - 미충족 (unsatisfied): 따르지 않고 있으며, 구체적 격차를 기록
   - 해당없음 (not applicable): 이 프로젝트에 적용되지 않는 패턴

3. 평가 결과를 산출물에 반영한다.
   - ARCHITECTURE.md: "권장 패턴 대비 현재 상태" 섹션
   - ANTI_PATTERNS.md: 미충족 격차 중 안티패턴 후보
   - VALIDATION.md: 패턴 충족 여부를 검증 기준에 포함

#### 규칙

- 평가는 비교 분석이지 강제 처방이 아니다. 하네스는 격차를 기록하되 변경을 명령하지 않는다.
- 프로젝트가 의도적으로 권장 패턴에서 일탈한 경우, 결함이 아닌 의식적 트레이드오프로 기록한다.
- 패턴 출처는 도메인 조사의 1차 근거 소스여야 하며, 블로그 단독 의견을 근거로 삼지 않는다.
- 프로젝트의 현재 구조/방법론을 맹목적으로 수용하지 않는다. 평가 없이 현 상태를 곧 권장으로 서술하는 것은 금지한다.

### 10. Anti/Good 쌍 작성

어댑터의 필수 쌍 목록과 contract packet의 프로젝트별 필수 쌍 목록에 있는 모든 케이스에 대해 Anti와 Good을 **반드시 쌍으로** 작성한다.

규칙:

- 한쪽만 있으면 불완전 상태로 판정한다.
- 각 쌍에는 케이스명을 명시하여 대응 관계가 명확해야 한다.
- 코드 관련 도메인은 나쁜 예시(코드 블록) + 권장 대체(코드 블록)를 포함한다.
- 비코드 도메인은 나쁜 사례(설명) + 권장 방법(설명)을 포함한다.
- 어댑터 최소 쌍 외에 contract packet에서 발견한 추가 쌍도 작성한다.
- example pack에 강한 직접 예시가 있다면, 거기서 패턴의 강도와 서술 밀도를 참고할 수 있다.

### 11. 강제 규칙 추출 (소프트웨어 도메인, 선택)

소프트웨어 도메인이고 contract packet에 스택이 감지된 경우에만 실행한다. 비소프트웨어 도메인은 이 단계를 건너뛴다.

절차:

1. 10단계에서 작성한 Anti/Good 쌍을 검토하여, **자동 검출 가능한 안티패턴**을 식별한다.
   - 린트 규칙으로 강제할 수 있는 패턴 (예: 미사용 변수, 잘못된 import 순서, 금지된 API 사용)
   - 정적 분석으로 강제할 수 있는 패턴 (예: 타입 안전성, 순환 의존성)

2. 해당 스택의 린트/정적 분석 도구에서 대응하는 규칙을 조사한다.
   - JavaScript/TypeScript: ESLint + 관련 플러그인
   - Python: Ruff, Flake8, mypy
   - Go: golangci-lint
   - 어댑터에 enforcement 도구가 명시되어 있으면 그것을 우선한다.

3. `enforcement/LINT_RULES.md`에 정리한다. 각 규칙에 대해:
   - 규칙 이름 (예: `react-hooks/exhaustive-deps`)
   - 심각도 (`error` 또는 `warn`)
   - 적용 근거 (어떤 안티패턴을 차단하는지)
   - 설정 코드 블록 (실제 설정 파일에 넣을 내용)

규칙:

- 이 단계의 산출물은 설정 **가이드 문서**(`.md`)다. 실제 설정 파일(`.eslintrc`, `ruff.toml` 등)은 구현 시 이 문서를 기반으로 생성한다.
- contract packet의 `enforcement_severity` 값에 따라 규칙 강도를 조절한다 (strict: 대부분 error, moderate: 핵심만 error 나머지 warn, minimal: 핵심만 warn).
- 프로젝트에 이미 린트 설정이 있으면 덮어쓰지 않고 보강 방향을 문서에 명시한다.

### 12. 산출물 작성

`.claude/skills/harness-<domain>-<name>.md`에 하네스 스킬을 작성하거나 보강한다.

`references/OUTPUT_CONTRACT.md`의 산출물 규칙을 따른다.

현재 작업 범위가 `engine-asset bootstrap`이거나 harness-engine 자체의 재사용 자산 보강이라면, 아래 경로도 함께 생성/수정할 수 있다.

- `references/adapters/<task_type>.md`
- `references/examples/<task_type>/README.md`
- `references/examples/<task_type>/ANTI_GOOD_REFERENCE.md`
- `references/examples/<task_type>/VALIDATION_REFERENCE.md`
- `references/stacks/<stack>.md` (해당 시)

최종 산출물은 단일 `.claude/skills/harness-<domain>-<name>.md` 파일이며, 다음 섹션을 포함한다:

- YAML frontmatter (name, description, user-invocable: true)
- 핵심 규칙 (아키텍처, 작업 흐름)
- 안티패턴 (Anti/Good 쌍)
- 검증 기준 (완료 조건, 체크리스트)

최소 섹션 계약:

- 무엇을 위한 하네스인가
- 언제 적용하는가
- 어떤 절차로 진행하는가
- 무엇을 금지하는가
- 무엇을 보면 완료라고 판단하는가
- 세션 재개 시 무엇을 읽으면 되는가
- 출처와 설계 근거가 어디에 있는가
- 프로젝트 전용 연결부를 어디에 두어야 하는가
- 현재 저장소 전용 예시를 코어 규칙으로 오해하지 않게 설명하는가
- contract packet에서 확정한 stack/library 규칙과 검증 포인트가 보이는가

### 13. 조사 근거 기록

조사한 근거를 세션 `notes/`에 기록한다. `session_path`의 notes/ 폴더에 항목을 추가한다.

## 산출물 형식

서브에이전트 완료 시 다음 정보를 본 에이전트에 반환한다.

1. **생성/수정된 파일 목록**: 경로와 각 파일의 역할
2. **실행 경로**: `project-harness generation` 또는 `engine-asset bootstrap`
3. **조사 근거 요약**: 사용한 1차 근거 소스와 핵심 발견
4. **Coverage 충족 상태**: 어댑터 최소 축과 contract packet 프로젝트 축별 충족 여부
5. **Anti/Good 쌍 충족 상태**: 최소 쌍과 프로젝트 쌍별 완성 여부
6. **Contract packet 사용 상태**: 어떤 packet을 읽었고 어떤 항목을 반영했는지
7. **선택형 example pack 사용 상태**: 어떤 example pack을 읽었고 무엇을 참고했는지
8. **Stack 반영 상태**: stack seed reference 사용 여부와 contract packet 반영 내용
9. **공통 phase 사용 상태**: common research phase와 bootstrap phase를 어떻게 적용했는지
10. **engine_followup_required**: `yes/no`와 사유
11. **미충족 항목**: 조사나 작성에서 충족하지 못한 항목 (있으면)
12. **Source Coverage Manifest 준수 상태**: manifest의 대상 하네스와 실제 생성 하네스의 일치 여부
13. **Cross-cutting 배포 상태**: cross-cutting 소스의 배포 지시 이행 여부와 배포 로그 경로

## 임시 파일 규칙

- 조사 중간 산출물, 임시 메모 등은 반드시 `session_path` 아래 `notes/` 폴더에 기록한다.
- 시스템 임시 디렉터리(`/tmp` 등)를 사용하지 않는다.
- 세션이 없는 환경에서는 프로젝트 루트의 `temps/`를 사용한다.

## 금지

- 세션 파일(SESSION.md)을 갱신하지 않는다 (본 에이전트 책임)
- `.claude/skills/use-skills.md`를 갱신하지 않는다 (본 에이전트 책임)
- 사용자에게 직접 질문하지 않는다 (본 에이전트가 사용자 상호작용 담당)
- contract packet 없이 생성 기준을 임의로 확정하지 않는다
- 최종 문서에 출처를 생략하지 않는다
- Anti/Good 쌍의 한쪽만 작성하고 완료로 처리하지 않는다
- 로컬 예시를 portable core 규칙으로 승격하지 않는다
- 시스템 임시 디렉터리(`/tmp`, `/var/tmp` 등)에 파일을 기록하지 않는다
