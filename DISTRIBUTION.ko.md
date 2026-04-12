# 배포 가이드

engine 플러그인을 배포하고 설치하는 방법을 안내합니다.

---

## 사용자: 플러그인 설치

### 빠른 설치 (2줄)

```bash
# 1. 이 저장소를 마켓플레이스로 추가
claude plugin marketplace add nwleedev/engine

# 2. engine 플러그인 설치
claude plugin install engine@engine
```

이것으로 완료입니다. 모든 Claude Code 세션에서 플러그인이 활성화됩니다.

### 설치 확인

```bash
# 설치된 플러그인 확인
claude plugin list

# 또는 Claude Code 내에서:
/plugin
```

`engine` 플러그인과 스킬(`/engine:deep-study`, `/engine:harness-engine` 등), 에이전트가 표시되어야 합니다.

### 업데이트

플러그인 관리자가 자동으로 업데이트를 처리합니다. 수동으로 확인하려면:

```bash
claude plugin update engine@engine
```

### 삭제

```bash
claude plugin uninstall engine@engine
```

---

## 팀: 자동 설치 프롬프트

프로젝트의 `.claude/settings.json`에 마켓플레이스를 추가하면 팀원에게 자동으로 설치를 안내합니다:

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

팀원이 프로젝트를 열고 신뢰(trust)하면 Claude Code가 자동으로 engine 플러그인 설치를 안내합니다.

---

## 조직: 관리형 설정

관리형 설정에서 `strictKnownMarketplaces`를 사용하면 조직 전체에 승인된 마켓플레이스만 허용할 수 있습니다:

```json
{
  "strictKnownMarketplaces": {
    "engine": {
      "source": { "source": "github", "repo": "nwleedev/engine" }
    }
  }
}
```

사용자가 비승인 마켓플레이스를 추가하는 것을 방지하면서 engine 플러그인은 사용할 수 있도록 합니다.

---

## 공식 Anthropic 마켓플레이스

### 제출

최대 가시성을 위해 공식 Anthropic 마켓플레이스에 제출할 수 있습니다:

- **Claude.ai**: [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)
- **Console**: [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)

승인되면 한 줄로 설치 가능합니다:

```bash
claude plugin install engine
```

### 요구사항

- `plugin.json`에 필수 필드 포함 (name, version, description, author)
- 품질 및 보안 심사 (구체적 기준은 비공개)
- 플러그인 이름은 kebab-case, 공백 불가

### 현재 상태

자체 호스팅 배포로 즉시 사용 가능합니다. 공식 마켓플레이스 제출은 더 넓은 배포가 필요할 때 진행할 수 있습니다.

---

## 배포 방법 비교

| 방법 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-----------|
| **GitHub 마켓플레이스** (자체 호스팅) | 즉시 배포, 승인 불필요 | 사용자가 `marketplace add` 필요 | 오픈소스, 소규모 팀 |
| **팀 settings.json** | 자동 안내, 마찰 최소 | 프로젝트별 설정 필요 | 사내 팀 |
| **관리형 설정** | 조직 전체 강제 | 관리자 권한 필요 | 기업 |
| **공식 마켓플레이스** | Discover 탭 노출, 최대 가시성 | 심사 필요, 기간 불명확 | 광범위 배포 |

---

## 로컬 개발

개발 중 변경사항을 테스트하려면:

```bash
# 설치 없이 직접 플러그인 디렉토리 로드
claude --plugin-dir ./engine

# 변경 후 리로드 (Claude Code 내에서)
/reload-plugins
```

`--plugin-dir`로 로드한 플러그인이 설치된 같은 이름의 플러그인보다 해당 세션에서 우선합니다.

---

## 프로젝트별 설정

설치 후 프로젝트의 `.claude/engine.env`를 생성하여 플러그인 동작을 커스터마이징할 수 있습니다:

```bash
# .claude/engine.env
REVIEW_AGENTS="도메인,구조"              # 리뷰 관점
RESEARCH_PERSPECTIVES="찬성,반대"        # 조사 관점
REVIEW_THRESHOLD_SINGLE=2               # 단일 리뷰 임계값
REVIEW_THRESHOLD_MULTI=5                # 병렬 리뷰 임계값
```

템플릿은 플러그인 내 `engine.env.example`에 포함되어 있습니다.
