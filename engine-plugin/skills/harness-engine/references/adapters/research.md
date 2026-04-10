# Research Task Adapter

## 목적

harness-engine이 조사 도메인 하네스를 생성하거나 보강할 때, 공통 `research` phase 이후 이 어댑터를 추가 적용하여 조사 task_type 고유의 **최소 계약**을 적용한다.

공통 `research` phase는 모든 task_type에 먼저 적용된다. 이 문서는 최종 `task_type`이 `research`일 때 필요한 추가 하한선을 정의한다.

## Coverage Contract

조사 하네스에는 다음 항목이 반드시 포함되어야 한다. 누락 시 하네스가 불완전한 것으로 판정한다.

### 필수 축 (모든 조사 프로젝트)

1. **Coverage Contract 정의**
   - 조사 주제마다 검토해야 할 공통 축 (최소 4개)
   - 도메인별 확장 축 정의 규칙
   - 비교 조사의 최소 비교 축 수
2. **Perspective Matrix**
   - 고정 목록이 아닌 기본 후보군 형태의 관점 체계
   - 주제별 관점 선택 규칙
   - 소프트웨어/비소프트웨어 분기 기준
3. **Source Fallback Rule**
   - 1차 근거 소스 우선순위 체계
   - 블로그 단독 근거 사용 금지 규칙
   - 마케팅 문구 취급 규칙
   - 최신성 확인 의무
4. **Claim-to-Evidence Map**
   - 주장별 근거 분리 기록 규칙
   - 고영향 주장의 독립 근거 요건 (2개 이상)
   - 근거 메모와 결론 분리 규칙
5. **Question-to-Evidence Budget**
   - 핵심 질문별 최소 증빙 예산 (1차 근거 + 보강 + 최신성)
   - 공식 문서 부재 시 처리 규칙
   - 미충족 시 표시 규칙
6. **Contradiction Rule**
   - 반대 근거 필수 기록 규칙
   - 비교 조사의 축별 오판 가능성 기록
   - 대체 불가 영역 분리 규칙

### 프로젝트 contract packet에서 반드시 조사할 항목

- 조사 주제에 맞는 비교 축 또는 판단 축
- 최신성 민감 항목
- 주제별 1차 근거 소스 묶음
- 결과를 미확정으로 남겨야 하는 조건

## 1차 근거 소스

조사 하네스의 Source Fallback Rule:

1. 공식 문서
2. 표준 문서
3. 실제 소스 코드
4. 공개 이슈 트래커, 벤더 기술 자료, 보조 자료

비소프트웨어 도메인의 경우:

1. 학술 논문, 정부/국제기구 공식 자료
2. 업계 표준 보고서, 전문 기관 발행 자료
3. 공개 데이터셋, 공식 통계
4. 전문 서적, 보조 자료

## 선택형 Example Pack

조사 task adapter는 아래 example pack을 참고할 수 있다.

- `references/examples/research/README.md`
- `references/examples/research/ANTI_GOOD_REFERENCE.md`
- `references/examples/research/VALIDATION_REFERENCE.md`

규칙:

- example pack은 규범 계약이 아니라 reference-only evidence다.
- example pack이 없어도 adapter 자체는 유효하다.
- 공통 `research` phase가 기본 조사 품질을 닫고, 이 adapter는 `research` task_type의 최소 산출물 요구를 닫는다.

## Anti/Good 최소 필수 쌍 목록

조사 하네스의 ANTI_PATTERNS.md에는 다음 케이스 각각에 대해 Anti와 Good 쌍이 **반드시** 존재해야 한다.

### 출처 관리

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 블로그 단독 근거 | 블로그 글 하나로 기술적 결론 확정 | 공식 문서로 확인 후 블로그는 보조로만 사용 |
| 마케팅 문구 인용 | 제품 마케팅 문구를 기술적 사실로 취급 | 마케팅 문구는 사용 방식 단서로만, 기술 결론은 공식 문서 기반 |
| 최신성 미확인 | 날짜 확인 없이 자료 인용 | 게시/수정 날짜, 버전, 현재 시점 재검색 포함 |

### 조사 폭

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 단일 검색 종료 | 첫 검색 결과만으로 결론 | Exploration Expansion Rule 적용, 관점 확장 |
| 편향된 결론 | 한 방향 근거만 수집 | Contradiction Rule 적용, 반대 근거 필수 기록 |
| 결론-근거 혼합 | 근거 메모와 최종 결론을 같은 문단에 작성 | Claim-to-Evidence Map으로 분리 기록 |

### 검색 실행

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 대량 검색 단일 턴 집중 | 5건 이상 검색을 단일 턴에서 병렬 실행 | 3~4건씩 배치로 나누어 실행, 배치마다 결과 요약 기록 |
| 무관 결과 방치 | 검색 결과를 필터 없이 전부 컨텍스트에 유지 | 무관한 대용량 결과 즉시 제외, 유관 항목만 인용 |

### 산출물

| 케이스 | Anti 내용 | Good 내용 |
|---|---|---|
| 템플릿 강제 평탄화 | 조사 내용을 템플릿에 맞추기 위해 억지로 변형 | 템플릿 선택 섹션으로 유연하게 구성 |
| 출처 생략 | 결론만 남기고 출처 미기재 | 최종 문서에 출처와 설계 근거 직접 포함 |

## 드라이런 입출력 예시

### Positive Case: Coverage Contract 적용 검증

**Input**: "React 상태 관리 라이브러리를 비교 조사해주세요."

**Expected Output (하네스가 안내해야 하는 방향)**:

- 비교 축 최소 2개 정의
- 각 비교 축마다 오판 가능성 1줄 이상
- Source Fallback Rule 적용
- Question-to-Evidence Budget 적용

### Negative Case: 출처 관리 위반 감지

**Input**: 조사 결과에 "X가 가장 빠르다"는 결론이 블로그 1개만으로 뒷받침되어 있음.

**Expected Output (하네스가 차단해야 하는 패턴)**:

- 블로그 단독 근거 → Anti-pattern으로 감지
- `미확정` 또는 `추가 조사 필요`로 표시 요구
- 공식 벤치마크 또는 독립 근거 보강 요구

## 비소프트웨어 도메인 확장

조사 대상이 소프트웨어가 아닌 경우:

- Perspective Matrix에서 소프트웨어 전용 관점 대신 도메인 적합 관점을 선택한다.
- Source Fallback Rule에서 "공식 문서 → 학술 자료 → 공개 데이터 → 보조 자료"로 대체한다.
- 도메인별 Coverage 축이 기존 체계로 설명 불가능하면 `references/common/BOOTSTRAP_PHASE.md`의 역할 정의 절차를 먼저 수행한다.

## 설계 근거

- Coverage Contract, Perspective Matrix, Source Fallback Rule: 레거시 research 하네스 분석 기반
- Anti/Good 필수 쌍 구조: OpenAI GPT-5 Prompting Guide + Anthropic eval 프레임워크
- Contradiction Rule, Claim-to-Evidence Map: 레거시 research 하네스의 교차검증 체계
