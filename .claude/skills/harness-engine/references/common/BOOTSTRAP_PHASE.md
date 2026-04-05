# Common Bootstrap Phase

## 목적

이 문서는 `harness-engine`이 공통 조사 phase 이후에도 Coverage 갭이 남거나, 미지 도메인을 만났을 때 실행하는 공통 bootstrap phase를 정의한다.

이 phase는 task adapter와 별개다. 역할은 다음 둘 중 하나다.

대표 분류에 adapter가 없을 때 엔진 자산까지 함께 만드는 경로는 이 문서가 아니라 `harness-engine`의 `engine-asset bootstrap` 실행 경로에서 다룬다.

- **신규 모드**: 대표 분류 집합으로 설명되지 않는 새 도메인의 초안 계약을 만든다.
- **보충 모드**: 기존 task adapter는 유지하되, 현재 프로젝트에 부족한 도메인 지식만 보충한다.

## 언제 사용하는가

### 신규 모드

- 대표 분류 집합(`frontend`, `research`, `backend`, `testing`, `security`, `ops`)으로 설명되지 않는다.
- 해당 도메인의 task adapter가 없다.
- 사용자가 새 도메인 하네스가 필요하다고 명시했다.

### 보충 모드

- task adapter는 있지만 Coverage 갭 체크에서 갭이 감지된다.
- task adapter의 방법론은 충분하지만, 현재 프로젝트의 구체적 지식이 부족하다.
- 예: `frontend` + 처음 보는 프레임워크, `research` + 처음 보는 산업/주제

## 필수 원칙

- human-in-the-loop 검증을 포함한다.
- bootstrap 결과는 기본적으로 초안 또는 보충 정보다.
- 현재 프로젝트 전용 예시와 실패 사례는 기본적으로 `local evidence pack` 후보다.
- 보충 모드에서는 기존 task adapter의 방법론(HOW)을 교체하지 않는다.
- bootstrap 결과는 project contract packet으로 먼저 정리하고, 그 뒤 하네스 산출물에 반영한다.

## 수행 절차

1. 역할 정의
   - Role, Goal, Backstory를 구체적으로 정의한다.
2. Coverage Contract 초안 생성
   - 핵심 축 최소 4개
   - 실패 모드 최소 3개
   - 1차 근거 소스
   - 품질 기준
3. 사용자 검증
   - 빠진 축, 불필요한 축, 실제 실패 사례, 추가 소스를 확인한다.
4. 보수적 기본값 명시
   - 사용자가 답하지 못한 항목은 보수적 기본값으로 채우고 표시한다.
5. 생성 단계로 전달
   - 확정한 Coverage, 실패 모드, 근거 소스, 품질 기준을 contract packet에 먼저 기록한다.
   - 신규 모드라면 정식 task adapter와 필요 시 example pack/seed asset까지 함께 만들 범위를 닫는다.

## 생성 단계로 넘겨야 하는 출력

- bootstrap mode: `new` 또는 `supplement`
- Role / Goal / Backstory
- 확정된 Coverage Contract
- 사용자 확인 결과
- 보수적 기본값 표시
- contract packet에 반영해야 할 필드
- 신규 모드라면 생성해야 할 adapter 경로와 필요 시 example/seed 자산 경로

## 실패 신호

- 미지 도메인인데 bootstrap 없이 바로 adapter나 하네스를 쓴다.
- 보충 모드인데 기존 adapter의 방법론 자체를 덮어쓴다.
- 사용자 검증 없이 generic 직책과 generic 품질 기준만 남긴다.
- bootstrap으로 얻은 local evidence를 portable core 규칙처럼 적는다.
