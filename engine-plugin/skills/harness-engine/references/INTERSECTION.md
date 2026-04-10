# Cross-Domain Intersection

## 목적

2개 이상의 하네스가 동일 프로젝트에서 공존할 때, 규칙 수준의 교차점을 사전에 감지하고, authority를 배정하고, 생성/검증 과정에서 일관되게 처리하기 위한 기준 문서다.

이 문서는 harness-engine의 Step 6.5(Intersection Scan), Step 7(Potential Intersection Discovery), Step 14.5(Cross-Harness Validation)에서 참조된다.

## 적용 시점

- 새 하네스를 생성하거나 기존 하네스를 보강할 때
- 대상 프로젝트에 `.claude/skills/harness-*.md` 파일이 1개 이상 이미 존재할 때
- Research Phase에서 현재 도메인과 교차 가능성이 높은 미생성 도메인을 식별할 때

## 기존 하네스 대상 감지 (Step 6.5)

### 3단계 휴리스틱

교차점 감지는 3단계로 수행하며, 비용이 낮은 단계부터 순서대로 적용한다. 각 단계에서 교차점이 발견되지 않으면 다음 단계로 넘어가지 않는다.

#### 단계 1: File Scope Overlap

두 하네스가 같은 파일 범위를 다루는지 확인한다.

- 비교 대상: frontmatter의 `matchPatterns.fileGlob`
- 판정: 두 glob 패턴이 겹치는 파일 집합이 있으면 overlap
- 비소프트웨어 도메인은 fileGlob이 없으므로 이 단계를 건너뛴다

#### 단계 2: Concept Keyword Overlap

두 하네스가 공유하는 개념이 있는지 확인한다.

- 비교 대상:
  - 기존 하네스의 `Intersection Metadata` 섹션의 `concept_keywords` (있으면)
  - 메타데이터가 없으면 규칙 제목, Anti/Good 케이스명에서 동적 추출
  - 새 하네스의 contract packet 필수 축, Anti/Good 필수 쌍 목록
- 정규화: 하이픈/언더스코어 통일, 복합어 분리 (예: `server-only` = `server_only` = `serveronly`)
- 판정 기준: **2개 이상** 공유 키워드가 있으면 교차점 후보로 분류
- false positive 허용: 사용자 확인 단계에서 걸러내므로, 감지 단계에서는 민감도를 높게 유지

#### 단계 3: Semantic Rule Analysis

공유 키워드가 있는 규칙들의 관계를 분류한다.

- **complementary**: 다른 관점에서 같은 개념을 다룸 (WHERE vs WHY, 구조 vs 보안). 양립 가능.
- **redundant**: 동일한 내용을 중복 서술. 하나를 canonical로 지정하고 다른 쪽은 참조로 전환.
- **contradictory**: 상충하는 지침. 사용자가 해결해야 하는 HARD CONFLICT.

분류 기준:
1. 두 규칙의 **대상**(WHAT)이 같고 **지시**(HOW)가 같으면 → redundant
2. 두 규칙의 **대상**(WHAT)이 같고 **관점**(WHY)이 다르면 → complementary
3. 두 규칙의 **대상**(WHAT)이 같고 **지시**(HOW)가 상충하면 → contradictory

## 잠재적 교차 도메인 발견 (Step 7 Research Phase 연동)

Research Phase에서 현재 생성 중인 도메인과 교차 가능성이 높은 **미생성 도메인**을 조사한다.

### 조사 방법

1. **공식 문서 키워드 추출**: 현재 도메인의 공식 문서가 언급하는 다른 도메인 키워드를 수집한다.
   - 예: FSD 문서가 "server-only", "security boundary" 언급 → security 도메인 교차 가능
   - 예: Backend 문서가 "rate limiting", "authentication" 언급 → security 도메인 교차 가능
2. **어댑터 known_intersections 힌트**: 어댑터에 `known_intersections` 섹션이 있으면 우선 참조한다.
3. **프로젝트 스택 기반 추론**: 현재 프로젝트의 기술 스택에서 교차 가능성이 높은 도메인을 추론한다.
   - 예: Next.js + API routes → security (입력 검증, CORS)
   - 예: React + SSR → performance (hydration, bundle size)
   - 예: Prisma + DB → security (SQL injection, data projection)
4. **기존 하네스의 potential_intersections**: 프로젝트의 기존 하네스에 `Potential Intersections` 메타데이터가 있으면, 현재 도메인이 거기에 언급되어 있는지 확인한다.

### 출력

조사 결과를 contract packet의 `## Potential Intersection Domains` 섹션에 기록한다.

```markdown
## Potential Intersection Domains

| 도메인 | 교차 개념 | 근거 | 기존 하네스 존재 |
|---|---|---|---|
| security | server-only, input-validation | FSD 공식 문서 보안 경계 섹션 | 없음 |
| testing | component-boundary | FSD 테스트 가이드 | 없음 |
```

### 사용자 상호작용

발견된 잠재적 교차 도메인을 사용자에게 제안한다:
- "이 도메인들과 교차할 가능성이 높습니다. 지금 함께 생성하시겠습니까?"
- 사용자가 선택하면 같은 세션에서 순차 생성 (현재 하네스 완료 후)
- 선택하지 않으면 하네스의 `Potential Intersections` 메타데이터에 기록하여 향후 참조

**제약**: 이 단계는 HARD GATE가 아닌 권고(SHOULD)다. 사용자가 무시해도 진행 가능하다.

## Authority 배정 규칙

교차점마다 authority를 배정하여, 어느 하네스가 해당 개념의 주 권한을 갖는지 결정한다.

### 배정 순서

1. 해당 개념이 어댑터 Coverage Contract의 **필수 축**에 있는 하네스 → `primary`
2. 양쪽 어댑터 모두 필수 축에 있으면 → 다음 기준 적용:
   - 필수 축에 직접 명시 vs Anti/Good에만 등장: 직접 명시한 쪽이 primary
   - 양쪽 모두 직접 명시: `shared` (다른 관점에서 같은 개념)
3. 양쪽 모두 필수 축에 없으면 → `user-decides`

### Authority 유형

| Authority | 의미 | 규칙 작성 방식 |
|---|---|---|
| `primary` | 이 하네스가 해당 개념의 canonical 규칙을 보유 | 전체 규칙 + 코드 예시 작성 |
| `secondary` | 다른 하네스가 primary | 자기 도메인 관점의 축약 규칙 + primary 참조 마커 |
| `shared` | 양쪽 모두 다른 관점에서 동일 개념을 다룸 | 각자 자기 관점의 전체 규칙 + 상호 참조 마커 |
| `user-decides` | 자동 결정 불가 | 사용자에게 선택지 제시 후 대기 |

## 참조 마커 형식

교차점에 해당하는 규칙에는 참조 마커를 추가하여, 규칙의 출처와 관계를 명시한다.

### Secondary Authority 마커

```markdown
> **Cross-Reference** — 이 규칙은 `harness-fe-fsd-module` Rule 7 (서버 전용 코드 FSD 배치)과 교차합니다.
> Primary authority: harness-fe-fsd-module (WHERE 관점). 이 하네스: WHY 관점.
```

### Shared Authority 마커

```markdown
> **Cross-Reference** — 이 규칙은 `harness-fe-security` Rule 9 (FSD shared 레이어 server-only 격리)과 교차합니다.
> Authority: shared. FSD 관점: 레이어 배치 규칙. Security 관점: 보안 격리 규칙.
```

## Anti/Good 쌍 배포 규칙

교차점에 해당하는 Anti/Good 쌍은 authority에 따라 배포한다.

| Authority | Anti/Good 작성 방식 |
|---|---|
| `primary` | 전체 Anti 코드 + 전체 Good 코드 포함 |
| `secondary` | 자기 도메인 관점의 축약 설명 + primary 참조. 코드 예시는 primary에 위임 가능 |
| `shared` | 각자 자기 도메인 관점의 전체 Anti/Good 쌍. 코드 예시가 동일해도 관점 설명이 다르면 양쪽 모두 유지 |

규칙:
- `secondary`가 코드 예시를 포함해도 되지만, primary와 중복되면 "코드 예시는 `harness-X` Case N 참조"로 축약 가능
- `shared`는 코드 예시가 동일하더라도 관점(WHY)이 다르므로 양쪽 유지를 기본으로 한다

## Intersection Map (contract packet 내 섹션)

Step 6.5의 감지 결과를 contract packet에 기록한다.

```markdown
## Intersection Map

### Detected Intersections

| 기존 하네스 | 감지 방법 | 공유 개념 | 관계 유형 |
|---|---|---|---|
| harness-fe-fsd-module | file-scope + concept | server-only, data-projection | complementary |
| harness-fe-testing | concept | input-validation | complementary |

### Resolution Directives

#### server-only (harness-fe-fsd-module × harness-fe-security)
- 관계: complementary
- FSD 관점: 서버 전용 코드의 레이어 배치 규칙
- Security 관점: `import "server-only"` 의무 선언 이유
- Authority: shared
- 조치: 양쪽 하네스에 상호 참조 마커 추가. 각자 자기 관점의 규칙 유지.
- Anti/Good: 양쪽 모두 전체 쌍 유지 (관점 차이)

### User Confirmation
- [확인됨] server-only: shared authority
- [확인됨] data-projection: FSD primary
```

교차점이 없으면:

```markdown
## Intersection Map

intersection_map: none
```

## Intersection Metadata (하네스 파일 내장 섹션)

하네스 파일(`.claude/skills/harness-*.md`)의 검증 기준 이후에 배치한다.

```markdown
## Intersection Metadata

concept_keywords: [keyword1, keyword2, keyword3]

### Declared Intersections
- with: harness-<other-domain>-<name>
  concepts: [shared-concept-1, shared-concept-2]
  authority: {shared-concept-1: shared, shared-concept-2: this}

### Potential Intersections
- <domain>: <concept1>, <concept2>
- <domain>: <concept3>
```

### 필드 설명

- `concept_keywords`: 이 하네스의 핵심 개념 목록. 규칙 제목, Anti/Good 케이스명, contract packet 필수 축에서 추출.
- `Declared Intersections`: 실제 감지되고 authority가 배정된 교차점. `with`는 교차 대상 하네스, `concepts`는 공유 개념, `authority`는 각 개념의 권한 (`this`/`other`/`shared`).
- `Potential Intersections`: Research Phase에서 발견했으나 아직 하네스가 생성되지 않은 잠재적 교차 도메인.

### 기존 하네스 호환

`Intersection Metadata` 섹션이 없는 기존 하네스는 "교차점 미선언"으로 취급한다:
1. Step 6.5에서 해당 하네스의 frontmatter(matchPatterns), 규칙 제목, Anti/Good 케이스명을 읽어 concept_keywords를 동적 추출
2. 추출된 키워드로 교차점 감지를 수행
3. 교차점이 발견되면 기존 하네스에 Intersection Metadata 섹션을 추가하는 "Pending Harness Update" 지시서를 생성

## Cross-Harness Validation (Step 14.5)

새로 생성된 하네스를 프로젝트 내 모든 기존 하네스와 대조한다.

### 검증 항목

1. **선언된 교차점 일치**: Intersection Metadata의 `Declared Intersections`가 실제 규칙 내용의 authority와 일치하는가
2. **참조 마커 존재**: authority가 secondary인 규칙에 참조 마커가 있는가. shared인 규칙에 상호 참조 마커가 있는가.
3. **미선언 교차점 감지** (HARD GATE): 3단계 휴리스틱으로 새로운 교차점을 스캔. 발견되면 Intersection Metadata 갱신 필요.
4. **모순 규칙 감지** (HARD GATE): contradictory로 분류되는 규칙 쌍이 있으면 사용자 해결 필요.
5. **메타데이터 상호 일관성**: 양쪽 하네스의 `Declared Intersections`가 서로를 참조하고 authority가 대칭인가 (A가 this이면 B는 other).
6. **Pending Harness Update**: 기존 하네스에 업데이트가 필요하면 지시서를 생성.

### 실패 신호

- 교차점이 감지됐으나 Intersection Metadata에 선언되지 않았다
- authority 배정과 실제 규칙 내용이 일치하지 않는다 (primary인데 축약만 있음)
- 양쪽 하네스의 Declared Intersections가 비대칭이다
- contradictory 교차점이 해결되지 않았다
- 참조 마커가 필요한 규칙에 누락되어 있다

## 비소프트웨어 도메인 대응

비소프트웨어 도메인(research, marketing, design-doc 등)은 file scope overlap이 적용되지 않는다.

- 단계 1(File Scope Overlap)을 건너뛰고 단계 2(Concept Keyword Overlap)부터 시작한다
- concept_keywords는 방법론, 프레임워크, 분석 기법 등에서 추출한다
  - 예: research 하네스의 키워드: [competitive-analysis, market-sizing, user-research]
  - 예: marketing 하네스의 키워드: [competitive-positioning, market-segmentation, AARRR]
  - 공유 키워드: competitive → 교차점 후보

## 금지

- 교차점 감지 결과를 사용자에게 보고하지 않고 자동 확정하기 (authority 배정은 사용자 확인 필수)
- contradictory 교차점을 해결하지 않고 하네스 생성 진행하기
- primary authority 하네스의 규칙을 secondary에서 그대로 복사하기 (참조 마커로 대체)
- Intersection Metadata를 하네스 파일 외부에 별도 파일로 관리하기
- 교차점이 없을 때 Intersection Metadata 섹션을 생략하기 (교차점 없어도 concept_keywords와 빈 Declared Intersections, Potential Intersections 하위 섹션을 포함한다)
