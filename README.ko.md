# Claude Code Harness System

Claude Code에 자동 규칙, 품질 게이트, 도메인 지식을 설치하는 설정/자동화 프레임워크.

> 코드 라이브러리가 아닙니다. Claude Code 위에 올라가는 **설정 레이어**입니다.

---

## 왜 필요한가?

| Claude Code 기본 상태 | Harness 적용 후 |
|---|---|
| 요청하면 바로 코딩/작성 시작 | 편집 전 **계획 수립을 강제** (훅이 차단) |
| 라이브러리 안티패턴을 반복 | 파일을 읽으면 **도메인 규칙을 자동 제안** |
| 대규모 변경이 리뷰 없이 통과 | 2-4개 단일 리뷰, 5+개 **병렬 품질 리뷰** |
| 긴 대화 후 맥락 상실 | 세션 종료/압축 시 **컨텍스트 자동 저장/복구** |
| 플랜 품질이 들쭉날쭉 | 플랜 완성 시 **완성도 자동 검증** |
| 위험한 git 명령 실수 가능 | `--force`, `reset --hard` 등 **파괴적 명령 차단** |

---

## 누구를 위한 시스템인가?

코딩뿐 아니라 리서치, 마케팅, 설계, 학습 등 **Claude Code를 사용하는 모든 작업**에 적용됩니다.

| 대상 | 예시 프로젝트 | 상세 안내 |
|------|-------------|----------|
| **프론트엔드 개발자** | React/Next.js 웹앱, UI 컴포넌트 라이브러리 | [Quick Start](.claude/docs/GETTING-STARTED.md#41-개발-프로젝트-프론트엔드) |
| **백엔드 개발자** | FastAPI REST API, Go 마이크로서비스 | [Quick Start](.claude/docs/GETTING-STARTED.md#42-개발-프로젝트-백엔드-python) |
| **리서처** | 시장조사, 경쟁사 분석, 기술 트렌드 | [Quick Start](.claude/docs/GETTING-STARTED.md#43-시장-조사-프로젝트) |
| **마케터** | 캠페인 기획, A/B 테스트 설계, 광고 카피 | [Quick Start](.claude/docs/GETTING-STARTED.md#44-마케팅-프로젝트) |
| **설계자** | 시스템 아키텍처 문서, RFC, ADR | [Quick Start](.claude/docs/GETTING-STARTED.md#45-설계-문서-프로젝트) |
| **학습자** | Kubernetes 입문, React 학습, ML 기초 | [Quick Start](.claude/docs/GETTING-STARTED.md#46-학습-프로젝트) |

---

## 설치

### 방법 1: 플러그인 설치 (권장)

> 프로젝트 파일 복사 없이 Claude Code 플러그인으로 설치합니다.

```bash
claude plugin install nwleedev/engine
```

프로젝트별 설정이 필요하면 `.claude/engine.env`를 생성하세요 (선택):

```bash
# .claude/engine.env
REVIEW_AGENTS="도메인,구조"              # 리뷰 관점 (쉼표 구분)
RESEARCH_PERSPECTIVES="찬성,반대"        # 조사 관점 (쉼표 구분)
```

### 방법 2: 독립 설치

> 프로젝트 `.claude/` 디렉토리에 전체 파일을 복사합니다.

```bash
# 프로젝트에 하네스 설치 (한 줄, git 불필요)
sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- ~/my-project

# Claude Code 실행
cd ~/my-project && claude
```

업데이트: `bash .claude/scripts/update.sh` 또는 같은 명령을 재실행하면 됩니다.

<details>
<summary>수동 설치 (git 사용)</summary>

```bash
git clone https://github.com/nwleedev/engine.git /tmp/engine
/tmp/engine/.claude/scripts/bootstrap.sh --source /tmp/engine --target ~/my-project
rm -rf /tmp/engine
cd ~/my-project && claude
```
</details>

### 비교

| 항목 | 플러그인 | 독립 설치 |
|------|---------|----------|
| 설치 | `claude plugin install` | curl 원라이너 |
| 업데이트 | 자동 (플러그인 관리자) | `update.sh` 수동 실행 |
| 여러 프로젝트 | 한 번 설치로 공유 | 프로젝트마다 설치 |
| 커스터마이징 | `.claude/engine.env` | `.claude/settings.local.json` |
| 스킬 접두사 | `/engine:deep-study` | `/deep-study` |

사전 요건: Claude Code CLI. 독립 설치 시 추가로 curl, tar, jq 필요. 상세 설치 방법은 [Getting Started](.claude/docs/GETTING-STARTED.md#1-사전-준비) 참조.

---

## 시스템 구성 요소

### Hooks (자동 실행)

| Hook | 트리거 | 동작 |
|------|--------|------|
| 플랜 강제 | 파일 편집 전 | 계획 없이 편집 시 차단 |
| 플랜 품질 검증 | 플랜 모드 종료 시 | 파일 존재, 필수 섹션, 모호성 자동 확인 |
| 하네스 제안 | 파일 읽기 후 | 파일 내용에서 도메인 키워드 감지 → 관련 규칙 제안 |
| 편집 추적 | 파일 편집 후 | 수정 파일 수 추적, 2-4개 단일 / 5+개 병렬 리뷰 |
| 세션 스냅샷 | 세션 종료 시 | 작업 상태를 `.claude/sessions/`에 저장 |
| 컨텍스트 복구 | 세션 시작/압축 시 | 이전 스냅샷에서 맥락 복원 |

### Skills (호출 시 활성)

| 스킬 | 호출 방법 | 용도 |
|------|----------|------|
| harness-engine | `/harness-engine` | 프로젝트 맞춤 도메인 규칙 자동 생성 |
| deep-study | `/deep-study` | 단계별 학습 프로토콜 (평가→설계→강의→검증) |
| failure-response | `/failure-response` | 에러 대응 방법론 (근본 원인 우선) |
| research-methodology | `/research-methodology` | 구조화된 리서치 프레임워크 |
| socratic-thinking | `/socratic-thinking` | 비판적 사고 원칙 (탐색 우선, 가정 검증) |

### Agents (자동/수동 호출)

| 에이전트 | 트리거 | 역할 |
|---------|--------|------|
| work-reviewer | 2-4개 단일 / 5+개 병렬 자동 | 변경사항 품질 리뷰 (관점 모드 지원) |
| plan-readiness-checker | 플랜 종료 시 자동 | 플랜 실행 가능성 검증 |
| turn-summarizer | 세션 종료 시 자동 | 턴 작업 서술형 요약 생성 |
| domain-professor | `/deep-study`로 수동 | 도메인 학습 프로페서 + 피드 생성 |
| harness-researcher | `/harness-engine` 내부 | 하네스 생성용 도메인 조사 |
| project-researcher | 수동 | 기술 선택, 아키텍처 결정 조사 (관점 모드 지원) |

### Scripts (자동화)

| 스크립트 | 용도 |
|---------|------|
| `bootstrap.sh` | 새 프로젝트에 하네스 환경 설치 |
| `sync.sh` | 코어 저장소 업데이트를 프로젝트에 반영 |
| `promote.sh` | 프로젝트 하네스를 코어 저장소로 승격 |
| `check-plan.sh` | 플랜 없이 편집 차단 (훅용) |
| `check-plan-review.sh` | 플랜 품질 검증 (훅용) |
| `suggest-harness.sh` | 파일 내용 기반 하네스 자동 제안 (훅용) |
| `track-edits.sh` | 편집 파일 수 추적, 리뷰어 트리거 (훅용) |
| `snapshot.sh` | 세션 스냅샷 저장 (훅용) |
| `update.sh` | 설치된 하네스를 최신 엔진 버전으로 업데이트 |
| `migrate.sh` | v1→v2 마이그레이션 |

---

## 핵심 개념

### 하네스 스킬

도메인별 규칙 파일(`.claude/skills/harness-*.md`)로, Claude가 해당 도메인에서 작업할 때 자동으로 참조한다. 처음엔 비어 있고, `/harness-engine`을 호출하면 프로젝트 스택을 분석해 맞춤 규칙을 자동 생성한다. 이후 관련 파일을 읽을 때마다 훅이 해당 하네스를 제안한다.

### 플랜 강제

모든 편집 작업 전에 계획 수립을 강제한다. Claude가 바로 코딩이나 작성을 시작하는 대신 `.claude/plans/`에 계획 파일을 먼저 만들고, 사용자 승인 후 실행한다. 비개발 작업(리서치, 마케팅 문서 등)에서도 동일하게 적용된다.

### 세션 연속성

대화가 길어지면 Claude Code가 이전 맥락을 압축하거나 잃을 수 있다. 이 시스템은 세션 종료와 압축 시점에 자동으로 스냅샷을 저장하고, 다음 세션이나 압축 후 자동으로 복원한다. 사용자가 직접 할 일은 없다.

---

## 문서 안내

| 문서 | 내용 |
|------|------|
| [Getting Started](.claude/docs/GETTING-STARTED.md) | 설치, 일상 사용법, 커스터마이징, 트러블슈팅, 아키텍처 |
| [Migration Guide](.claude/docs/MIGRATION.md) | v1→v2 마이그레이션 안내 |
| [CLAUDE.md](CLAUDE.md) | 프로젝트 규칙 (Claude가 읽는 파일) |
| [CLAUDE.md.example](.claude/CLAUDE.md.example) | 새 프로젝트용 CLAUDE.md 템플릿 |

---

## 프로젝트 구조

```
.claude/
  engine.env          # 플러그인 설정 (선택, 리뷰/조사 관점 등)
  settings.json          # 훅 설정 (시스템 관리, 수정 불필요)
  settings.local.json    # 프로젝트별 권한/훅 커스터마이징
  scripts/               # 9개 자동화 스크립트
  skills/                # 6개 스킬 + harness-engine 서브시스템
  agents/                # 6개 전문 에이전트
  docs/                  # Getting Started, Migration
  plans/                 # 작업 계획 (자동 생성)
  sessions/              # 세션 스냅샷 (자동 생성)
```

직접 편집이 필요한 파일은 **3개뿐**: `CLAUDE.md`(프로젝트 규칙), `.claude/settings.local.json`(권한 설정), `.claude/engine.env`(플러그인 설정, 선택).

---

## 업데이트 및 동기화

### 방법 1: 프로젝트에서 직접 업데이트 (권장)

```bash
# 업데이트 확인만
bash .claude/scripts/update.sh --check

# 변경 미리보기
bash .claude/scripts/update.sh --dry-run

# 업데이트 실행
bash .claude/scripts/update.sh

# 로컬 엔진 레포에서 오프라인 업데이트
bash .claude/scripts/update.sh --source ~/engine

# 특정 버전으로 업데이트
bash .claude/scripts/update.sh --version v1.2.0
```

### 방법 2: install.sh 재실행

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/nwleedev/engine/main/install.sh)" -- ~/my-project
```

업데이트가 관리하는 것: 훅 스크립트, settings.json, 범용 스킬, 에이전트, CLAUDE.md 코어 영역.
업데이트가 건드리지 않는 것: 프로젝트 규칙, 도메인 하네스, 세션/플랜 데이터, settings.local.json.

---

## 커밋 컨벤션

```
<type>(<scope>): <subject>
```

type: `feat`, `fix`, `refactor`, `docs`, `chore` 등.
