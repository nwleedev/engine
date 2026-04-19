# domain-professor

모든 도메인에 대한 구조화된 학습 자료를 생성합니다. `/teach`로 교재를 직접 생성하거나, 플러그인이 세션 기록에서 낯선 도메인을 자동으로 감지하여 학습을 제안합니다.

## 작동 방식

domain-professor는 두 가지 훅을 실행하고 두 가지 명령어를 제공합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시마다 | 최근 세션 요약에서 낯선 도메인 용어를 스캔하고 보고 |
| `Stop` | 세션 종료 시마다 | 세션 중 등장한 도메인 감지 |

교재는 `.claude/textbooks/<domain>/`에 생성됩니다:

```
.claude/textbooks/<domain>/
├── INDEX.md
├── 01-overview/
│   └── what-is-<domain>.md
├── 02-core-concepts/
│   └── <concept>.md
└── 03-advanced/
    └── <concept>.md
```

각 파일은 파인만 기법을 따릅니다: 쉬운 언어로 된 요약, 핵심 개념, 실제 예시, 선수 학습 링크.

## 설치

```
/plugin marketplace add nwleedev/domain-professor
```

또는 전체 engine 마켓플레이스를 설치합니다:

```
/plugin marketplace add nwleedev/engine
```

## 사용법

### /teach

```
/teach <domain>
/teach <domain> <concept>
```

예시:

```
/teach kubernetes
/teach kubernetes pod scheduling
/teach react server components
```

- 교재가 없으면: `01-overview/what-is-<domain>.md`와 `INDEX.md`를 생성합니다.
- 교재가 있고 개념을 지정하지 않은 경우: 기존 내용을 검토하고 다음 단계를 제안합니다.
- 개념을 지정한 경우: 해당 단계의 개념 파일을 생성합니다. 이미 존재하면 `/teach-more`를 제안합니다.

### /teach-more

```
/teach-more <path>
```

기존 개념 파일을 더 깊이 다룹니다:

```
/teach-more .claude/textbooks/kubernetes/01-overview/what-is-kubernetes.md
```

3~5개의 세부 개념 파일이 있는 하위 폴더를 생성하고, 원본 파일에 "Further Reading" 섹션을 추가합니다. `INDEX.md`를 업데이트합니다.

## 설정

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DOMAIN_PROFESSOR_LANGUAGE` | `English` | 생성되는 교재 내용의 언어 |
| `DOMAIN_PROFESSOR_DOMAINS` | _(비어 있음)_ | 자동 감지할 도메인의 쉼표 구분 목록. 비어 있으면 모든 도메인이 대상 |

예시 `.env`:

```
DOMAIN_PROFESSOR_LANGUAGE=Korean
DOMAIN_PROFESSOR_DOMAINS=kubernetes,react,fastapi
```
