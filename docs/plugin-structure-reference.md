# Claude Code Plugin Structure Reference

> 조사 기준: superpowers 5.0.7, plugin-dev (unknown), slack 1.0.0, figma 2.1.7, security-guidance (unknown)
> 작성일: 2026-04-16

---

## 공식 플러그인 폴더 구조

```
<plugin-name>/
├── .claude-plugin/              ★ 필수
│   ├── plugin.json              ★ 필수 — 플러그인 매니페스트
│   └── marketplace.json         선택 — 마켓플레이스 메타데이터
│
├── agents/                      선택 — 에이전트 정의
│   └── <agent-name>.md
│
├── commands/                    선택 — 슬래시 명령 진입점 (사용자가 /name:cmd 로 호출)
│   └── <command-name>.md
│
├── hooks/                       선택 — 훅 설정 및 스크립트
│   ├── hooks.json               훅 이벤트 → 명령 매핑
│   ├── run-hook.cmd             선택 — Windows 훅 실행기
│   └── <event-name>/            선택 — 이벤트별 스크립트 디렉토리
│       └── <script>             (superpowers 패턴: hooks/session-start/)
│
├── skills/                      선택 — 스킬 구현
│   └── <skill-name>/
│       ├── SKILL.md             ★ 스킬 진입점 (frontmatter + 지침)
│       ├── references/          선택 — 참조 문서
│       │   └── *.md
│       ├── examples/            선택 — 예제
│       │   └── *.md
│       └── scripts/             선택 — 스킬 전용 스크립트
│           └── *.sh
│
├── templates/                   선택 — 프로젝트 템플릿 파일
│   └── *.example
│
├── docs/                        선택 — 플러그인 문서
├── tests/                       선택 — 테스트
├── scripts/                     선택 — 릴리스/유틸리티 스크립트 (훅 외)
│
├── .cursor-plugin/              선택 — Cursor IDE 지원
│   └── plugin.json
├── .cursor-mcp.json             선택 — Cursor MCP 설정
├── .mcp.json                    선택 — MCP 서버 설정
├── .opencode/                   선택 — OpenCode 지원
├── .codex/                      선택 — Codex 지원
├── .github/                     선택 — GitHub 통합
│
├── CLAUDE.md                    선택 — Claude Code 지침
├── GEMINI.md                    선택 — Gemini 지침
├── gemini-extension.json        선택 — Gemini 확장 설정
├── package.json                 선택 — Node.js 패키지 (의존성 있을 때)
├── README.md                    권장
└── LICENSE                      권장
```

---

## `plugin.json` 필드

**위치:** `.claude-plugin/plugin.json`

```json
{
  "name": "plugin-name",
  "description": "한 줄 설명",
  "version": "1.0.0",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "homepage": "https://github.com/org/repo",
  "repository": "https://github.com/org/repo",
  "license": "MIT",
  "keywords": [
    "keyword1",
    "keyword2"
  ]
}
```

| 필드 | 필수 | 설명 |
|---|---|---|
| `name` | ★ | 플러그인 식별자 (소문자, 하이픈) |
| `description` | ★ | 한 줄 설명 |
| `version` | ★ | 시맨틱 버전 (X.Y.Z) |
| `author` | 권장 | 이름 + 이메일 객체 |
| `homepage` | 권장 | 문서/GitHub URL |
| `repository` | 권장 | 소스 코드 URL |
| `license` | 권장 | SPDX 라이선스 식별자 (예: "MIT") |
| `keywords` | 권장 | 검색 및 분류용 태그 배열 |

---

## `commands/` vs `skills/` 구분

공식 플러그인은 사용자 노출 명령과 구현 로직을 분리함:

### `commands/<name>.md` — 슬래시 명령 진입점

사용자가 `/plugin:name` 으로 직접 호출하는 얇은 파일. 로직 없음, 스킬로 위임.

```markdown
---
description: "명령 설명 (명령 팔레트에 표시됨)"
argument-hint: "[선택적 인자]"
---

Use the plugin:skill-name skill to complete this command.
```

### `skills/<name>/SKILL.md` — 전체 스킬 구현

실제 지침, 절차, 규칙이 담긴 파일. `user-invocable: true` frontmatter로 직접 호출도 가능.

```markdown
---
name: skill-name
description: "스킬 설명 (Skill 도구에서 선택 시 표시됨)"
user-invocable: true
---

# Skill Title
...
```

**규칙:** `commands/`는 발견 가능성을 위한 진입점, `skills/`는 실제 구현. 중복 없이 위임만 함.

---

## 훅 스크립트 위치 관례

**핵심 규칙:** hook에서 직접 호출하는 스크립트는 `hooks/` 디렉토리 내에 위치.

### superpowers 패턴 (이벤트별 서브디렉토리)

```
hooks/
├── hooks.json
├── run-hook.cmd         # Windows 실행기
└── session-start/       # 이벤트별 디렉토리
    └── <scripts>
```

### engine 패턴 (scripts/ 서브디렉토리)

```
hooks/
├── hooks.json
└── scripts/             # 모든 훅 스크립트
    ├── session-restore.sh
    ├── check-plan.sh
    ├── inject-harness.sh
    └── lib/             # 소스 전용 라이브러리
        └── harness-match.sh
```

**주의:** `scripts/` 디렉토리를 플러그인 루트에 두는 것은 비표준. 훅 외 유틸리티 스크립트(릴리스, 버전 범프 등)는 루트 `scripts/`에 두어도 무방하나, 훅에서 직접 호출하는 스크립트는 `hooks/` 안에 위치해야 함.

---

## `templates/` 관례

프로젝트에 복사될 예제 파일은 `templates/` 하위에 위치:

```
templates/
├── CLAUDE.md.example
├── CLAUDE.md.ko.example    # 언어별 변형
└── engine.env.example
```

`setup` 스킬이 이 파일들을 읽어 프로젝트에 복사함. `${CLAUDE_PLUGIN_ROOT}/templates/<file>` 경로로 참조.

---

## `${CLAUDE_PLUGIN_ROOT}` 이식성 규칙

`hooks.json`의 command 경로는 반드시 `${CLAUDE_PLUGIN_ROOT}` 변수로 시작해야 함:

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/session-restore.sh"
}
```

하드코딩 금지:
```json
// ❌ 하드코딩 금지
"command": "/Users/alice/.claude/plugins/cache/engine/engine/1.0.7/hooks/scripts/session-restore.sh"
```

---

## `lib/` 서브디렉토리 관례

셸 스크립트에서 여러 스크립트가 공유하는 함수는 `lib/` 에 위치:

```
hooks/scripts/
├── inject-harness.sh    # source "$SCRIPT_DIR/lib/harness-match.sh"
└── lib/
    └── harness-match.sh  # 직접 실행 불가, source 전용
```

**규칙:**
- `lib/` 스크립트는 직접 실행되지 않음 — source 또는 import 전용
- `hooks.json`의 command 배열에 `lib/` 스크립트 직접 등록 금지
- 스크립트는 `dirname "${BASH_SOURCE[0]}"` 로 자신의 위치를 기준으로 `lib/` 를 참조

---

## 스킬 SKILL.md frontmatter 필드

```markdown
---
name: skill-name                    ★ 필수
description: "설명"                 ★ 필수 (Skill 도구에서 표시)
user-invocable: true                선택 — 사용자가 직접 호출 가능
model: sonnet|haiku|opus            선택 — 기본값: 상속
effort: low|medium|high             선택
maxTurns: 200                       선택
tools:                              선택 — 허용 도구 목록
  - Read
  - Grep
disallowedTools:                    선택 — 금지 도구 목록
  - Write
  - Edit
---
```

---

## 에이전트 frontmatter 필드

```markdown
---
name: agent-name
description: "에이전트 설명 (Agent 도구에서 subagent_type으로 선택)"
model: sonnet
effort: high
maxTurns: 200
tools:
  - WebSearch
  - Read
disallowedTools:
  - Write
---
```

---

## 참고: 조사한 플러그인 목록

| 플러그인 | 버전 | 특징 |
|---|---|---|
| superpowers | 5.0.7 | agents, commands, hooks, skills, tests, docs |
| plugin-dev | unknown | agents, commands, skills (references/examples/scripts 서브디렉토리) |
| slack | 1.0.0 | commands, skills, MCP 설정, CLAUDE.md |
| figma | 2.1.7 | skills, .cursor-plugin, .github |
| security-guidance | unknown | hooks만 있는 최소 구성 |
| code-review | unknown | commands만 있는 최소 구성 |
