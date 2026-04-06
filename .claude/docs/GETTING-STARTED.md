# Claude Code Harness System — Getting Started

## 0. 이 시스템은 무엇인가?

Claude Code는 터미널에서 실행하는 AI 코딩 어시스턴트다. 기본 상태로도 강력하지만, **프로젝트에 맞는 규칙과 자동화를 설정하면 품질이 크게 올라간다.**

이 시스템("Harness System")은 Claude Code가 다음을 **자동으로** 수행하도록 만든다:

| 자동 동작 | 설명 | 없으면 어떻게 되나 |
|---|---|---|
| **플랜 강제** | 코드/문서 편집 전 반드시 계획 수립 | Claude가 바로 코딩 시작 → 방향 틀어짐 |
| **도메인 규칙 제안** | 파일을 읽으면 관련 규칙 자동 표시 | 라이브러리 안티패턴 모르고 반복 |
| **편집 추적** | 수정한 파일 수를 추적하고 3개+ 시 리뷰어 호출 | 대규모 변경이 리뷰 없이 통과 |
| **세션 스냅샷** | 대화 종료 시 컨텍스트 자동 저장 | 컨텍스트 압축 후 방향 상실 |
| **플랜 품질 검증** | 플랜 완성 시 파일 존재 여부, 필수 섹션 자동 확인 | 실행 불가능한 플랜으로 작업 시작 |

### 비개발자에게: 왜 이게 필요한가?

Claude Code는 코딩뿐 아니라 **리서치, 마케팅 문서, 설계 문서, 학습** 등에도 사용할 수 있다. 이 시스템이 하는 일은:
- 조사하기 전에 **계획을 먼저 세우게** 강제
- 관련 **방법론과 체크리스트를 자동으로 제안**
- 긴 작업 중 대화가 길어져도 **맥락을 자동 보존**
- 산출물을 **독립적으로 검토**

---

## 1. 사전 준비

### 1.1 Claude Code 설치

```bash
# Claude Code CLI 설치
curl -fsSL https://claude.ai/install.sh | bash

# 설치 확인
claude --version
```

또는 VS Code, JetBrains IDE 확장, 데스크톱 앱, 웹(claude.ai/code)에서 사용 가능.

### 1.2 필수 도구

```bash
# jq (JSON 처리 — 하네스 제안 스크립트에서 사용)
brew install jq        # macOS
sudo apt install jq    # Ubuntu/Debian

# Git (세션 관리에 필요)
git --version
```

### 1.3 선택적 도구 (프로젝트 유형별)

| 프로젝트 유형 | 추가 도구 |
|---|---|
| 프론트엔드 개발 | Node.js, pnpm/npm, Lefthook (`npx lefthook install`) |
| 백엔드 Python | Python 3.10+, ruff, mypy |
| 백엔드 Go | Go 1.21+, golangci-lint |
| 비개발 (리서치 등) | 추가 도구 불필요 |

---

## 2. 새 프로젝트에 세팅하기

### 2.1 부트스트랩 (한 번만)

```bash
# 프로젝트 디렉터리 생성 (또는 기존 프로젝트로 이동)
mkdir ~/my-project && cd ~/my-project
git init  # Git 초기화 (이미 되어 있으면 생략)

# 부트스트랩 실행
~/.claude-harness/.claude/scripts/bootstrap.sh --target .
```

> 프로젝트 유형별 하네스는 부트스트랩 후 `/harness-engine`을 호출하면 자동 생성됩니다.

### 2.2 부트스트랩 후 생성되는 파일

```
my-project/
├── CLAUDE.md                          # ← 프로젝트별 규칙 작성 (마커 아래)
└── .claude/
    ├── settings.json                  # 훅 설정 (수정 불필요)
    ├── settings.local.json            # ← 프로젝트별 권한 커스터마이징
    ├── scripts/                       # 자동화 스크립트 (수정 불필요)
    │   ├── check-plan.sh
    │   ├── check-plan-review.sh
    │   ├── suggest-harness.sh
    │   ├── track-edits.sh
    │   ├── snapshot.sh
    │   ├── sync.sh
    │   ├── bootstrap.sh
    │   ├── promote.sh
    │   └── migrate.sh
    ├── skills/
    │   ├── core-rules.md              # 범용 규칙 (수정 불필요)
    │   ├── failure-response.md
    │   ├── deep-study.md
    │   ├── research-methodology.md
    │   ├── socratic-thinking.md
    │   ├── harness-engine/            # 하네스 생성 엔진 (수정 불필요)
    │   └── harness-*.md               # 프로젝트별 하네스 (harness-engine이 생성)
    ├── agents/
    │   ├── work-reviewer/             # 코드/문서 리뷰 에이전트
    │   ├── domain-tutor/              # 학습 에이전트
    │   ├── harness-researcher/        # 도메인 조사 에이전트
    │   ├── harness-auditor/           # 설정 평가 에이전트
    │   ├── plan-readiness-checker/    # 플랜 품질 검증 에이전트
    │   └── project-researcher/        # 프로젝트 리서치 에이전트
    ├── docs/
    │   ├── GETTING-STARTED.md         # 설치 및 사용 가이드
    │   └── MIGRATION.md               # v1→v2 마이그레이션
    ├── plans/                         # 작업 계획 파일 (자동 생성)
    └── sessions/                      # 세션 스냅샷 (자동 생성)
```

**직접 편집해야 하는 파일은 2개뿐:**
1. `CLAUDE.md` — 프로젝트별 규칙 (마커 아래만)
2. `.claude/settings.local.json` — 권한 설정

### 2.3 CLAUDE.md 프로젝트 영역 작성

부트스트랩 후 `CLAUDE.md`에 아래 마커가 있다:

```markdown
<!-- HARNESS-SYNC-CORE-END -->
<!-- HARNESS-SYNC-PROJECT-START -->

## 여기에 프로젝트별 규칙 작성
```

**마커 위(CORE 영역)는 수정하지 마세요** — `sync.sh`가 관리합니다.
**마커 아래(PROJECT 영역)에 프로젝트별 규칙을 작성합니다.**

예시 (리서치 프로젝트):
```markdown
<!-- HARNESS-SYNC-PROJECT-START -->

## Research Rules
- All research outputs go to docs/ directory
- Always cite sources with URLs and dates
- Use MECE framework for competitor analysis
```

예시 (개발 프로젝트):
```markdown
<!-- HARNESS-SYNC-PROJECT-START -->

## Stack
- Python 3.12 + FastAPI + SQLAlchemy 2.0
- PostgreSQL 16, Redis 7

## Testing
- pytest with fixtures in tests/conftest.py
- Always run: pytest tests/ -x --tb=short
```

### 2.4 MCP 서버 설정

MCP 서버는 Claude Code가 외부 도구를 사용할 수 있게 한다. 아래는 권장 서버 목록이다.

```bash
# 웹 검색 (리서치 프로젝트에 필수)
claude mcp add tavily-mcp -- npx -y tavily-mcp

# 라이브러리 문서 (개발 프로젝트에 필수)
claude mcp add context7 -- npx -y @upstash/context7-mcp

# 브라우저 자동화 (프론트엔드에 권장)
claude mcp add playwright -- npx -y @playwright/mcp@latest

# Notion 연동 (문서 관리에 유용)
claude mcp add notion -- npx -y @notionhq/notion-mcp-server

# 구조화된 사고 (복잡한 분석)
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

---

## 3. 일상 사용법

### 3.1 작업 시작 — 항상 플랜부터

Claude Code를 시작하고 작업을 요청하면, **자동으로 플랜 모드가 강제**된다.

```
$ claude
> "사용자 인증 API를 구현해줘"

# Claude가 .claude/plans/ 에 계획 파일을 생성
# 계획이 승인되면 구현 시작
# 플랜 없이 바로 코드를 쓰려 하면 → 훅이 차단
```

비개발 프로젝트에서도 동일:

```
> "한국 핀테크 시장 경쟁사 분석을 해줘"

# Claude가 리서치 계획 수립 (범위, 방법론, 산출물 정의)
# 계획 승인 후 조사 시작
```

### 3.2 하네스 스킬 — 도메인 규칙 자동 제안

파일을 읽으면 관련 하네스 스킬이 자동 제안된다:

```
# React Hook Form 코드를 읽었을 때:
> 관련 harness 스킬이 감지되었습니다:
> • /harness-fe-react-hook-form (React Hook Form 감지)
```

**처음엔 하네스가 없다.** 첫 세션에서 `/harness-engine`을 호출하면 프로젝트에 맞는 하네스가 생성된다:

```
> "/harness-engine"
> "이 프로젝트의 FastAPI와 SQLAlchemy 패턴에 맞는 하네스를 만들어줘"

# → .claude/skills/harness-be-fastapi.md 생성
# → .claude/skills/harness-be-sqlalchemy.md 생성
# 이후 관련 파일 읽을 때 자동 제안
```

### 3.3 학습 모드 — 모르는 기술 배우기

```
> "/deep-study"
> "React Query를 기초부터 배우고 싶어"

# domain-tutor 에이전트가 활성화
# 1. 현재 수준 평가 (퀴즈)
# 2. 맞춤 커리큘럼 설계
# 3. 단계별 강의 + 실습
# 4. 이해도 검증
```

비개발 주제도 가능:
```
> "/deep-study"
> "마케팅 퍼널 분석을 배우고 싶어"
```

### 3.4 작업 리뷰 — 자동 품질 검토

3개 이상의 파일을 수정하면 **work-reviewer 에이전트가 자동 호출**된다:

```
# 파일 3개 수정 후:
> [work-reviewer] 변경사항을 검토합니다...
> - 원본 요구사항과 일치하는가
> - 코드 품질 (보안, 안티패턴)
> - 하네스 규칙 준수 여부
```

### 3.5 세션 관리 — 맥락 자동 보존

| 이벤트 | 자동 동작 |
|---|---|
| 대화 종료 (Stop) | `.claude/sessions/<id>/SESSION.md`에 작업 상태 저장 |
| 컨텍스트 압축 (Compact) | 압축 직전 상세 스냅샷 저장 → 압축 후 자동 복구 |
| `/clear` 후 재시작 | 이전 세션 스냅샷 표시 → 맥락 이어가기 |
| 새 세션 시작 | 가장 최근 플랜 파일 경로 안내 |

**사용자가 할 일은 없다** — 모두 자동이다.

---

## 4. 프로젝트 유형별 Quick Start

### 4.1 개발 프로젝트 (프론트엔드)

```bash
~/.claude-harness/.claude/scripts/bootstrap.sh --target .
claude mcp add context7 -- npx -y @upstash/context7-mcp
claude mcp add playwright -- npx -y @playwright/mcp@latest
npx lefthook install

claude
> "/harness-engine"
> "React, TanStack Query, Zustand 패턴에 맞는 하네스를 만들어줘"
```

### 4.2 개발 프로젝트 (백엔드 Python)

```bash
~/.claude-harness/.claude/scripts/bootstrap.sh --target .
claude mcp add context7 -- npx -y @upstash/context7-mcp
npx lefthook install

claude
> "/harness-engine"
> "FastAPI + SQLAlchemy 패턴 하네스를 만들어줘"
```

### 4.3 시장 조사 프로젝트

```bash
mkdir ~/research/market-analysis && cd ~/research/market-analysis
git init
~/.claude-harness/.claude/scripts/bootstrap.sh --target .
claude mcp add tavily-mcp -- npx -y tavily-mcp

claude
> "한국 SaaS B2B 시장 규모와 주요 플레이어를 조사해줘"
```

### 4.4 마케팅 프로젝트

```bash
~/.claude-harness/.claude/scripts/bootstrap.sh --target .
claude mcp add tavily-mcp -- npx -y tavily-mcp

claude
> "/harness-engine"
> "디지털 마케팅 캠페인 기획과 A/B 테스트 하네스를 만들어줘"
```

### 4.5 설계 문서 프로젝트

```bash
~/.claude-harness/.claude/scripts/bootstrap.sh --target .

claude
> "마이크로서비스 인증 시스템 설계 문서를 작성해줘"
```

### 4.6 학습 프로젝트

```bash
~/.claude-harness/.claude/scripts/bootstrap.sh --target .

claude
> "/deep-study"
> "Kubernetes를 기초부터 체계적으로 배우고 싶어"
```

---

## 5. 커스터마이징

### 5.1 하네스 자동 제안 — `matchPatterns` 프론트매터

하네스 스킬에 `matchPatterns`를 추가하면 파일을 읽을 때 자동으로 해당 하네스가 제안된다. 별도 설정 파일이 필요 없다.

```yaml
---
name: harness-be-fastapi
description: Use when working with FastAPI — APIRouter, Depends, HTTPException...
user-invocable: true
matchPatterns:
  fileGlob: "^.*/src/.*\.py$"
  regex:
    - "FastAPI|APIRouter|Depends|HTTPException"
---
```

- `fileGlob`: 이 패턴에 매칭하는 파일 경로에서만 제안 (선택)
- `regex`: 파일 내용에서 매칭할 정규식 배열 (하나라도 매칭 시 제안)
- `matchPatterns`가 없으면 description의 키워드로 자동 폴백 매칭

`/harness-engine`으로 생성된 하네스에는 자동으로 `matchPatterns`가 포함된다.

### 5.2 `.claude/settings.local.json` — 권한과 프로젝트 훅

Claude Code가 어떤 명령을 확인 없이 실행할 수 있는지 설정한다. **프로젝트 고유 훅도 이 파일에 추가** — `settings.json`의 훅과 자동 병합된다.

```json
{
  "permissions": {
    "deny": ["Bash(git commit --no-verify*)"],
    "allow": ["WebSearch", "Bash(pytest:*)", "Bash(git:*)"]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/scripts/my-custom-hook.sh\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### 5.3 프로젝트 고유 스킬/에이전트/스크립트 추가

| 구성요소 | 추가 방법 | sync에서 안전한가 |
|---|---|---|
| **스킬** | `.claude/skills/harness-*.md` 생성 | 안전 (비관리 파일) |
| **에이전트** | `.claude/agents/<name>/AGENT.md` 생성 | 안전 (화이트리스트 외) |
| **훅** | `.claude/settings.local.json`에 추가 | 안전 (비관리 파일) |
| **스크립트** | `.claude/scripts/` 에 추가 | 안전 (화이트리스트 외) |

> sync.sh는 명시적 화이트리스트만 관리합니다. 프로젝트에서 자유롭게 추가한 파일은 sync에서 무시됩니다.

### 5.4 프로젝트 → 코어 역반영 (promote)

프로젝트에서 만든 유용한 파일을 다른 프로젝트에서도 사용하고 싶다면:

```bash
# 도메인 하네스 → 카테고리 예제로 승격
~/.claude-harness/.claude/scripts/promote.sh \
  --source ~/my-api \
  --file .claude/skills/harness-be-fastapi.md \
 

# 범용 스킬 → 코어로 승격
~/.claude-harness/.claude/scripts/promote.sh \
  --source ~/my-api \
  --file .claude/skills/core-auth-rules.md \
  --destination core

# 확인만 (실제 복사 안 함)
promote.sh ... --dry-run
```

---

## 6. 인프라 업데이트 받기

`~/.claude-harness/` 저장소가 업데이트되면 프로젝트에 반영한다:

```bash
cd ~/.claude-harness && git pull

# 각 프로젝트에 동기화
~/.claude-harness/.claude/scripts/sync.sh --target ~/projects/my-api
~/.claude-harness/.claude/scripts/sync.sh --target ~/research/my-analysis

# 확인만 (변경 없이)
sync.sh --target ~/projects/my-api --dry-run
```

**sync가 변경하는 것:** 훅 스크립트, settings.json, 범용 스킬, 하네스 엔진, 에이전트, CLAUDE.md CORE 영역

**sync가 변경하지 않는 것:** CLAUDE.md PROJECT 영역, 도메인 하네스, 세션/플랜 데이터, 패턴 JSON, settings.local.json, lefthook.yml, 프로젝트 고유 스크립트/에이전트

---

## 7. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| "플랜 파일이 없습니다" 에러로 편집 차단 | 정상 동작 | Shift+Tab으로 플랜 모드 진입 또는 `/plan` 입력 |
| 하네스 제안이 안 나옴 | matchPatterns 없음 또는 fileGlob 미매칭 | 스킬 프론트매터 확인 (matchPatterns 없으면 description 폴백) |
| `jq: command not found` | jq 미설치 | `brew install jq` (macOS) |
| 세션 복구 안 됨 | `.claude/sessions/` 디렉터리 없음 | `mkdir -p .claude/sessions` |
| sync 후 CLAUDE.md 내용 사라짐 | PROJECT 영역에 마커 없음 | `<!-- HARNESS-SYNC-PROJECT-START -->` 마커 추가 |
| work-reviewer 안 나옴 | 3개 미만 파일 수정 | 정상 동작 (3개+ 에서만 트리거) |
| pre-commit 훅 안 됨 | Lefthook 미설치 | `npx lefthook install` |

---

## 8. 시스템 구성 요소 한눈에 보기

```
사용자 입력
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Claude Code CLI / IDE / Desktop / Web              │
│                                                      │
│  ┌─── Hooks (자동 실행) ──────────────────────────┐  │
│  │  SessionStart  → 세션 스냅샷 복구               │  │
│  │  PreToolUse    → 플랜 강제 + 플랜 품질 검증      │  │
│  │  PostToolUse   → 하네스 제안 + 편집 추적          │  │
│  │  Stop          → 세션 스냅샷 저장                │  │
│  │  PreCompact    → 압축 전 상세 스냅샷              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── Skills (호출 시 활성) ──────────────────────┐  │
│  │  core-rules.md           범용 규칙              │  │
│  │  failure-response.md     에러 대응              │  │
│  │  deep-study.md           학습 프로토콜          │  │
│  │  research-methodology.md 리서치 프레임워크      │  │
│  │  socratic-thinking.md    비판적 사고 원칙       │  │
│  │  harness-engine/         하네스 생성 팩토리     │  │
│  │  harness-<domain>-*      도메인별 규칙          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── Agents (자동/수동 호출) ─────────────────────┐ │
│  │  work-reviewer         3개+ 파일 수정 시 자동   │ │
│  │  plan-readiness-checker 플랜 종료 시 자동 검증  │ │
│  │  domain-tutor          /deep-study로 학습       │ │
│  │  harness-researcher    하네스 생성 시 조사 위임  │ │
│  │  harness-auditor       설정 품질 감사           │ │
│  │  project-researcher    기술/아키텍처 조사       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─── MCP Servers (외부 도구) ─────────────────────┐ │
│  │  context7     라이브러리 문서                    │ │
│  │  tavily       웹 검색/크롤링                    │ │
│  │  playwright   브라우저 자동화                    │ │
│  │  notion       노트/문서 관리                    │ │
│  │  figma        디자인↔코드 브릿지                 │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 9. FAQ

**Q: CLAUDE.md에 뭘 써야 하나요?**
A: Claude가 코드/파일만 보고는 알 수 없는 것만 쓰세요. 프로젝트 컨벤션, 특이한 의사결정, 사용 중인 외부 서비스 정보 등. 150줄 이하로 유지하세요.

**Q: 하네스 스킬은 직접 만들어야 하나요?**
A: 아닙니다. `/harness-engine`을 호출하면 Claude가 프로젝트를 분석하고 자동으로 생성합니다. 직접 수정도 가능합니다.

**Q: 플랜 강제를 끄고 싶으면?**
A: `.claude/settings.json`에서 `PreToolUse`의 `Write|Edit` 훅을 제거하면 됩니다. 하지만 권장하지 않습니다 — 플랜 없는 작업은 방향을 잃기 쉽습니다.

**Q: 비개발 프로젝트에서 pre-commit이 없어도 괜찮나요?**
A: 네. pre-commit은 코드 린트/타입체크용입니다. 비개발 프로젝트에서는 work-reviewer 에이전트가 품질 검토를 담당합니다.

**Q: MCP 서버 없이도 사용할 수 있나요?**
A: 네. MCP 서버는 선택사항입니다. 하지만 개발 프로젝트에서 context7(라이브러리 문서), 리서치 프로젝트에서 tavily(웹 검색)는 강력히 권장합니다.

**Q: 팀원과 환경을 공유하려면?**
A: `~/.claude-harness/`를 GitHub에 push하세요. 팀원이 clone 후 `bootstrap.sh`를 실행하면 됩니다. 프로젝트별 `.claude/` 디렉터리는 프로젝트 저장소에 커밋하여 공유합니다.

**Q: 프로젝트에서 만든 하네스를 다른 프로젝트에서도 쓰고 싶으면?**
A: `promote.sh`로 코어 저장소에 승격하세요. 도메인 하네스는 자동으로 카테고리 예제로 분류됩니다.
