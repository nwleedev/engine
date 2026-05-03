# codex-quality-guard

`codex-quality-guard`는 작업 턴이 superficial한 방식으로 끝났는지 점검하는 Codex 플러그인이다.

Codex 훅을 사용하지 않는다. 대신 재사용 가능한 스킬과 AGENTS.md 지침을 제공한다.

- `codex-quality-guard:retrospect`는 현재 턴의 superficial 작업 여부를 회고한다.
- `codex-quality-guard:install`은 AGENTS.md에 추천 회고 지침이 있는지 검사한다.

## 스킬

### `codex-quality-guard:retrospect`

작업 턴을 마치기 전에 사용한다. 코드 또는 파일 변경이 있는 턴에서 특히 강하게 적용한다.

출력 형식은 다음과 같다.

```text
Context status: complete | reconstructed | incomplete
Superficial risk: none | low | medium | high | unknown
Evidence sources:
- current conversation: used | unavailable
- AGENTS.md: used | unavailable
- project artifacts: used | unavailable
- git status/diff: used | unavailable
- user-provided summary: used | unavailable
- optional session memory: used | unavailable | mismatch
Evidence:
- ...
Root-cause check:
- ...
Next action:
- ...
```

`retrospect`는 Codex `/review`를 대체하지 않는다. `/review`는 diff 결함을 검토하고, `retrospect`는 현재 턴의 작업 방식을 회고한다.

### `codex-quality-guard:install`

AGENTS.md를 검사할 때 사용한다.

```bash
python3 plugins/codex-quality-guard/skills/install/install.py
```

명령은 다음 상태 중 하나를 출력한다.

- `installed`
- `partial`
- `missing`
- `not found`

installer는 진단 전용이다. 추천 블록을 출력하지만 AGENTS.md를 직접 수정하지 않는다.
