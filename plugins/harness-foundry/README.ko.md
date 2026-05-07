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
- development, non-development, mixed work를 모두 설계 대상으로 다룹니다.
- 파일 생성과 설정 활성화는 사용자 명시 승인 후 별도 단계로 진행합니다.

## 포함된 Skills

- `diagnose-project`
- `design-domain-harness`
- `update-registry`
- `scaffold-domain-harness`
- `audit-domain-harness`

## 검증

설치된 plugin 사용자는 공개 skill surface와 프로젝트 로컬
`docs/domain-harness/**` 산출물을 다룹니다. 사용자 프로젝트의
`docs/domain-harness/**` 파일을 검증하려면 이 저장소의 skill-local
read-only validator를 실행합니다.

```bash
rtk python3 plugins/harness-foundry/skills/audit-domain-harness/scripts/validate_domain_harness.py <project-root>
```

Maintainer 전용 plugin package 검증과 corpus 검증은
`apps/harness-foundry-lab`에 있으며, lab 명령은 해당 app README를 참고합니다.
