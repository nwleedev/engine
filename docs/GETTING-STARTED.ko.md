# 시작하기

> [English](GETTING-STARTED.md)

이 엔진은 **Claude Code 플러그인**으로 배포된다. 이 문서는 설치, 최초 사용, 프로젝트별 설정을 다룬다.

## 사전 준비

- Claude Code CLI ([설치 문서](https://docs.claude.com/en/docs/claude-code))
- 프로젝트 디렉터리에서 실행 중인 Claude Code 세션

그 외 별도 도구는 필요 없다. 플러그인에 모든 구성 요소가 포함된다.

## 설치

```bash
claude plugin marketplace add nwleedev/engine
claude plugin install engine@engine
```

설치 확인:

```bash
claude plugin list
```

`engine` 플러그인이 스킬(`/engine:deep-study`, `/engine:harness-engine` 등)과 에이전트와 함께 표시되어야 한다.

업데이트·삭제는 플러그인 매니저가 담당한다:

```bash
claude plugin update engine@engine
claude plugin uninstall engine@engine
```

### 로컬 개발

플러그인 자체를 개발하는 경우 로컬 체크아웃을 가리킬 수 있다:

```bash
claude --plugin-dir ./engine
```

세션 중 변경 사항을 반영하려면 `/reload-plugins` 를 실행한다.

### 팀 자동 설치

프로젝트의 `.claude/settings.json` 에 마켓플레이스를 등록하면, 팀원이 프로젝트를 신뢰할 때 자동으로 설치를 제안받는다:

```json
{
  "extraKnownMarketplaces": {
    "engine": {
      "source": { "source": "github", "repo": "nwleedev/engine" }
    }
  },
  "enabledPlugins": {
    "engine@engine": true
  }
}
```

조직 단위 관리 설정은 [DISTRIBUTION.md](../DISTRIBUTION.md) 참조.

## 최초 사용 — 플랜 워크플로우

플러그인이 활성화되면 Claude Code 동작이 달라진다:

- **편집 전 플랜 모드 강제**. "사용자 인증 구현" 같은 요청은 Claude 가 먼저 `.claude/plans/` 하위에 플랜 파일을 작성하도록 만든다. 승인 전 관점별 체커가 플랜을 검토한다.
- **도메인 규칙 자동 제안 — 하네스 생성 이후**. `/engine:harness-engine` 으로 프로젝트별 하네스 스킬(`.claude/skills/harness-*.md`)을 생성한 뒤부터, 관련 파일을 읽으면 해당 스킬이 자동 제안된다. 생성 전에는 제안이 동작하지 않는다.
- **편집 추적**. 2개 이상 파일 수정 시 단일 `work-reviewer` 실행. 5개 이상이거나 인프라 파일이 1개 이상 포함된 2+ 수정 시 멀티 관점 리뷰. 임계값은 `REVIEW_THRESHOLD_SINGLE` / `REVIEW_THRESHOLD_MULTI` 로 재정의 가능.
- **세션 스냅샷**. 세션 종료·압축 직전 `.claude/sessions/<id>/SESSION.md` 에 상태를 저장하고, 다음 세션에서 자동 복구.
- **파괴적 git 명령 차단**. `--no-verify`, `--force` push, `reset --hard`, `clean -f`, `branch -D`, `checkout -- .` 은 명시적 우회가 없으면 차단된다.

별도 설정 없이 동작한다. 설치 후 평소처럼 Claude Code 를 사용하면 된다.

## 프로젝트별 설정

기본 리뷰·리서치 관점을 바꾸려면 프로젝트에 `.claude/engine.env` 를 생성한다:

```bash
# .claude/engine.env
WORK_REVIEW_PERSPECTIVES="도메인,구조,요구사항"
PLAN_REVIEW_PERSPECTIVES="플랜구조,작업단계,요구사항"
RESEARCH_PERSPECTIVES="pro,con"
REVIEW_THRESHOLD_SINGLE=2
REVIEW_THRESHOLD_MULTI=5
```

모든 변수는 선택적이며, 플러그인에 담긴 기본값은 `engine.env.example` 에 문서화돼 있다. 관점 값은 자유 형식이라 한국어 토큰도 그대로 사용 가능하다.

플러그인에 템플릿이 포함되어 있으니 복사해 편집하면 된다.

프로젝트 고유 권한·훅·에이전트는 `.claude/settings.json` 과 `.claude/settings.local.json` 에 둔다. 런타임에 플러그인 훅과 병합되므로, 플러그인이 제공하는 파일은 직접 수정할 필요가 없다.

## 도메인 규칙 생성

`/harness-engine` 은 스택을 분석해 맞춤 하네스 스킬을 만든다:

```
/engine:harness-engine
> FastAPI + SQLAlchemy 백엔드용 하네스를 만들어줘
```

생성된 스킬은 플러그인 외부인 프로젝트의 `.claude/skills/harness-*.md` 에 저장되므로 레포에 같이 커밋된다. 각 스킬에 `matchPatterns` 이 선언돼 있어, 관련 파일을 읽을 때 자동 제안 훅이 올바른 규칙을 찾아낸다.

## 유형별 Quick Start

### 프론트엔드

```
/engine:harness-engine
> React + TanStack Query + Zustand 하네스 생성
```

### 백엔드 (Python)

```
/engine:harness-engine
> FastAPI + SQLAlchemy 2.0 하네스 생성
```

### 리서치

```
> 한국 B2B SaaS 시장 규모와 주요 플레이어를 조사해줘
```

플랜 강제는 동일하게 적용된다 — Claude 가 범위·방법론을 정의하고 출처를 명시한 뒤 조사한다.

### 학습

```
/engine:deep-study
> Kubernetes 기초부터 가르쳐줘
```

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| "No plan files found" 으로 편집 차단 | 정상 동작 | 플랜 모드 진입(Shift+Tab) 또는 `/plan` 입력 |
| 하네스 제안이 뜨지 않음 | `matchPatterns` 없음 / `fileGlob` 미매칭 | 스킬 프론트매터 확인. description 키워드가 폴백으로 동작 |
| 세션 복구 안 됨 | `.claude/sessions/` 부재 | `mkdir -p .claude/sessions` |
| work-reviewer 미실행 | 수정 파일 1개 이하 | 정상 — 2개부터 실행 |
| multi-review 미실행 | 5개 미만 + 인프라 변경 없음 | 정상 — 5+개 또는 인프라 포함 시 실행 |

## FAQ

**Q. `.claude/` 에 여전히 뭔가 설치해야 하나?**
아니다. 플러그인은 자체 완결형이다. 사용자는 원하는 것만 `.claude/` 에 추가하면 된다 — 오버라이드용 `engine.env`, 권한용 `settings.local.json`, 프로젝트 고유 스킬·에이전트 등.

**Q. 플랜 강제를 끄려면?**
권장하지 않지만, `.claude/settings.local.json` 에 특정 matcher 의 플랜 훅을 억제하는 오버라이드를 둘 수 있다. 기본값이 존재하는 이유는 플랜 없는 편집이 금방 방향을 잃기 때문이다.

**Q. 다른 플러그인과 충돌하면?**
스킬은 네임스페이스가 적용된다(`/engine:<skill>`). 에이전트도 마찬가지(`engine:<agent>`). 충돌은 설계상 회피된다.

**Q. 하네스를 프로젝트 간 공유하려면?**
`.claude/skills/harness-*.md` 를 프로젝트 레포에 커밋하라. 플러그인 외부 파일이므로 코드와 함께 이동한다.

## 참고: 스킬과 에이전트

| 스킬 | 호출 | 용도 |
|---|---|---|
| setup | `/engine:setup` | 템플릿에서 `CLAUDE.md`, `engine.env` 초기화 |
| harness-engine | `/engine:harness-engine` | 프로젝트별 도메인 규칙 생성 |
| deep-study | `/engine:deep-study` | 단계별 학습 프로토콜 |
| failure-response | `/engine:failure-response` | 에러 대응 방법론 |
| research-methodology | `/engine:research-methodology` | 구조화된 리서치 프레임워크 |
| socratic-thinking | `/engine:socratic-thinking` | 비판적 사고 원칙 |

| 에이전트 | 트리거 | 역할 |
|---|---|---|
| work-reviewer | 편집 수·인프라 임계값 자동 | 변경 품질 리뷰 (단일 또는 관점 병렬) |
| plan-readiness-checker | 플랜 종료 시 자동 | 플랜 실행 가능성 검증 |
| turn-summarizer | 세션 종료 시 자동 | 서술형 턴 요약 |
| domain-professor | `/engine:deep-study` | 도메인 학습 |
| harness-researcher | `/engine:harness-engine` | 하네스 생성용 도메인 조사 |
| project-researcher | 수동 디스패치 | 기술·아키텍처 조사 |

---

프로젝트 개요는 [README](../README.ko.md), 배포 옵션은 [DISTRIBUTION.md](../DISTRIBUTION.md) 참조.
