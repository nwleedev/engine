# domain-professor

모든 도메인에 대한 구조화된 학습 자료를 생성합니다. `/teach`로 교재를 직접 생성하거나, 플러그인이 세션 기록에서 낯선 도메인을 자동으로 감지하여 학습을 제안합니다.

## 작동 방식

domain-professor는 세 가지 훅을 실행하고 세 가지 명령어를 제공합니다:

| 훅 | 실행 시점 | 동작 |
|---|---|---|
| `SessionStart` | 세션 시작 시마다 | professor 플래그를 초기화하고 교재 목차를 컨텍스트에 주입 |
| `UserPromptSubmit` | 활성화 중 모든 프롬프트 | professor SKILL.md를 컨텍스트에 주입하여 학습 모드를 유지 |
| `Stop` | 세션 종료 시마다 | 트랜스크립트에서 도메인을 감지하고 교재 파일을 생성 |

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

### /toggle

현재 세션에서 professor 모드를 활성화하거나 비활성화합니다.

```
/domain-professor:toggle
```

- **활성화** 상태: 모든 프롬프트에 professor 역할이 주입되어 작업 중에도 지속적으로 학습 모드가 유지됩니다.
- **비활성화** 상태: professor 모드가 꺼집니다. Stop 훅은 계속 실행되지만 교재 생성을 건너뜁니다.

### /teach

professor 모드에서 자유 형식의 작업을 수행하고 관련 도메인의 교재 파일을 생성합니다.

```
/teach <자유 형식 작업 설명>
```

예시:

```
/teach kubernetes pod 스케줄링이 어떻게 작동하는지 설명해줘
/teach 디바운스 입력을 위한 React 훅을 작성해줘
/teach 금융에서 옵션 가격 책정이란 무엇인가요?
```

도메인을 식별하고, 작업을 수행하며, `.claude/textbooks/<domain>/` 아래에 파일을 생성하거나 업데이트합니다.

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

예시 `.env`:

```
DOMAIN_PROFESSOR_LANGUAGE=Korean
```
