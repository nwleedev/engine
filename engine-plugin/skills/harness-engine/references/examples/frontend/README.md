# Frontend Reference Example Pack

이 디렉터리는 현재 저장소의 레거시 프론트엔드 하네스와 직접 예시에서 추린 reference-only evidence를 담는다.

목적:

- 프론트엔드 하네스가 어느 정도의 직접 예시와 validation 강도를 가져야 하는지 보여준다.
- `React`, `TanStack Query`, `React Hook Form` 같은 흔한 조합에서 어떤 Anti/Good 쌍이 필요한지 빠르게 떠올리게 한다.
- Feature Sliced Design(FSD)을 채택한 프로젝트에서 public API, layer rule, cross-import가 어떤 밀도로 문서화되어야 하는지 보여준다.
- thin frontend adapter와 project contract packet을 보조하는 few-shot reference 역할을 한다.

규칙:

- 여기 있는 내용은 새 프로젝트에 그대로 복사할 portable core가 아니다.
- 프로젝트 스택과 맞지 않는 내용은 참고만 하고 버린다.
- 최종 문서의 출처와 규칙은 항상 해당 프로젝트의 공식 문서와 실제 코드 기준으로 다시 확정한다.
- 이 디렉터리는 최소 계약의 기준선이 아니다. 최소 계약 판정은 common phase, adapter, contract packet 기준을 우선한다.

관련 레거시 evidence 문서:

- `.claude/skills/harness-fe-tanstack-query.md`
- `.claude/skills/harness-fe-react-hook-form.md`
- `.claude/skills/harness-fe-testing.md`
- `.claude/skills/harness-fe-testing.md`
- `.claude/skills/harness-fe-fsd.md`
