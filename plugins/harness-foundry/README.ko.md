# harness-foundry

프로젝트별 `domain-harness`를 설계하기 위한 Codex-first skills 모음입니다.

## 목적

`harness-foundry`는 팀이 프로젝트를 진단하고, 도메인별 AI 작업 환경을 설계하며, 사람이 읽을 수 있는 registry를 관리하고, 안전한 스캐폴딩을 계획하며, 기존 harness 산출물을 감사하도록 돕습니다.

`harness-foundry`는 공개 skills/subagents를 대량 설치하는 도구가 아니라, 현재 프로젝트의 도메인에 맞는 `domain-harness`를 설계하고 검증하도록 돕는 Codex-first plugin입니다.

영어 README와 `SKILL.md`가 canonical 문서이며, 이 한국어 문서는 한국어 사용자를 위한 보조 설명입니다.

## 경계

- v1은 skill-only plugin입니다.
- agents, MCP servers, hooks, AGENTS.md rules를 자동 설치하지 않습니다.
- 공개 awesome repository를 bulk-install하지 않습니다.
- development, non-development, mixed work를 모두 지원합니다.
- 현업 프로젝트의 report는 project-local 산출물입니다.
- GitHub issue/PR template은 대상 프로젝트에 설치 승인을 받기 전까지 passive asset입니다.

## 포함된 Skills

- `diagnose-project`
- `design-domain-harness`
- `update-registry`
- `scaffold-domain-harness`
- `audit-domain-harness`

## 검증

실행:

```bash
rtk python3 plugins/harness-foundry/scripts/validate_harness_foundry.py
rtk python3 plugins/harness-foundry/scripts/validate_domain_harness.py plugins/harness-foundry/fixtures/domain-harness/valid-dev
rtk pytest plugins/harness-foundry/tests
```

## 현업 프로젝트 품질 루프

대상 프로젝트에서는 `docs/domain-harness/index.md`를 source of truth로 사용합니다. validator는 대상 프로젝트 루트에 대해 실행할 수 있습니다.

```bash
rtk python3 plugins/harness-foundry/scripts/validate_domain_harness.py <project-root> --json
```

validator JSON은 improvement report 초안으로 변환할 수 있습니다.

```bash
rtk python3 plugins/harness-foundry/scripts/summarize_domain_harness_failures.py validation.json
```

report 초안은 민감정보 제거 여부를 검토한 뒤 사용자가 승인할 때만 대상 프로젝트에 저장합니다. 저장 위치는 다음을 권장합니다.

```text
docs/domain-harness/reports/<date>-improvement-report.md
```

upstream fixture 후보는 synthetic, public-safe case로 축소된 경우에만 `engine`에 반영합니다.

## 현업 프로젝트 적용 모델

| 모델 | 기본값 | 설명 |
|---|---|---|
| Operator-run | 예 | `engine` 또는 plugin cache의 script를 대상 프로젝트 루트에 대해 실행합니다. |
| Project-local tooling | 아니오 | 명시 승인 후에만 대상 프로젝트에 tooling을 복사합니다. |
| Plugin-mediated workflow | 아니오 | Codex plugin/skill 환경에서 진단, scaffold, audit을 진행합니다. |

v1 권장값은 Operator-run입니다. 대상 프로젝트에 tooling을 복사하기 전에 진단과 report 초안을 만들 수 있기 때문입니다.

현업 프로젝트의 report는 자동 저장하지 않습니다. 초안을 검토하고 민감정보 제거와 사용자 승인을 거친 뒤에만 `docs/domain-harness/reports/<date>-improvement-report.md`에 저장합니다.

GitHub issue/PR template, AGENTS.md, MCP 설정, hooks, subagents는 별도 승인 전에는 설치하거나 활성화하지 않습니다.

상세 절차는 영어 canonical 문서인 `references/downstream-adoption-guide.md`를 기준으로 합니다.
