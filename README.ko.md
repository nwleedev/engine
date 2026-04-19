# engine

세션 연속성, 도메인 학습, 리서치 품질, 계획 준수를 강제하는 4개의 Claude Code 플러그인입니다. 각 플러그인은 독립적으로 설치하여 사용할 수 있습니다.

## engine이란?

engine은 Claude Code 플러그인 마켓플레이스로, 네 가지 품질 강화 플러그인을 개발 환경에 설치합니다. 이 플러그인들은 Claude가 세션 간 컨텍스트를 유지하고, 필요 시 도메인 전문 지식을 습득하며, 답변 전에 리서치 주장을 검증하고, 프로젝트별 코딩 표준을 준수하도록 보장합니다.

각 플러그인은 독립적으로 설치할 수 있어 필요한 것만 선택해 사용할 수 있습니다.

## 플러그인

| 플러그인 | 설명 |
|---|---|
| [session-memory](plugins/session-memory/README.ko.md) | 세션 시작 시 최근 3개 세션 요약을 자동으로 요약하고 주입합니다 |
| [domain-professor](plugins/domain-professor/README.ko.md) | 원하는 도메인에 대한 구조화된 학습 자료를 생성합니다 |
| [better-research](plugins/better-research/README.ko.md) | 가설 → 출처 → 반론 → 근본 원인 → 최종 답변의 5단계 리서치 프로토콜을 강제합니다 |
| [harness-engineer](plugins/harness-engineer/README.ko.md) | 도메인별 코딩 표준을 주입하고 세션 종료 시 위반 사항을 감지합니다 |

## 빠른 설치

4개의 플러그인을 한 번에 설치합니다:

```
/plugin marketplace add nwleedev/engine
```

## 개별 설치

플러그인을 개별적으로 설치하려면 각 플러그인의 README를 참고하세요:

- [session-memory](plugins/session-memory/README.ko.md)
- [domain-professor](plugins/domain-professor/README.ko.md)
- [better-research](plugins/better-research/README.ko.md)
- [harness-engineer](plugins/harness-engineer/README.ko.md)

## 요구 사항

플러그인 마켓플레이스를 지원하는 Claude Code.
