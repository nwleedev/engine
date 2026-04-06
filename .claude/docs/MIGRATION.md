# Migration Guide — v1 → v2

## 변경 사항

| 항목 | v1 (구 레이아웃) | v2 (새 레이아웃) |
|---|---|---|
| 스크립트 위치 | `claude-scripts/` (프로젝트 루트) | `.claude/scripts/` |
| 패턴 파일 | `suggest-harness-patterns.json` (프로젝트 루트) | 하네스 스킬 프론트매터 `matchPatterns` |
| 부트스트랩 | `--category` 필수 | 카테고리 없음 (harness-engine이 동적 생성) |
| 템플릿 | `templates/<category>/` | 삭제됨 |
| 훅 경로 | `$CLAUDE_PROJECT_DIR/claude-scripts/X` | `$CLAUDE_PROJECT_DIR/.claude/scripts/X` |
| 부트스트랩 호출 | `~/.engine/claude-scripts/bootstrap.sh` | `~/.engine/.claude/scripts/bootstrap.sh` |
| docs 위치 | `~/.engine/docs/` | `~/.engine/.claude/docs/` |

## 마이그레이션 방법

### 자동 마이그레이션 (권장)

```bash
# 1. 변경 사항 미리보기
~/.engine/.claude/scripts/migrate.sh --target <project-path> --dry-run

# 2. 실행
~/.engine/.claude/scripts/migrate.sh --target <project-path>
```

`migrate.sh`가 수행하는 작업:
1. `claude-scripts/*.sh` → `.claude/scripts/` 이동
2. `.claude/settings.json` 훅 경로 업데이트
3. `suggest-harness-patterns.json` 제거
4. 빈 `claude-scripts/` 디렉터리 제거
5. 최신 코어 파일 동기화 (harness-auditor 등 새 에이전트 포함)

### 수동 마이그레이션

```bash
cd <project-path>

# 1. 스크립트 이동
mkdir -p .claude/scripts
mv claude-scripts/*.sh .claude/scripts/
rmdir claude-scripts

# 2. settings.json 경로 업데이트
sed -i '' 's|claude-scripts/|.claude/scripts/|g' .claude/settings.json

# 3. 패턴 파일 제거
rm -f suggest-harness-patterns.json

# 4. 최신 코어 동기화
~/.engine/.claude/scripts/sync.sh --source ~/.engine --target .
```

## matchPatterns 프론트매터 추가

v1에서는 `suggest-harness-patterns.json`에 패턴을 정의했습니다.
v2에서는 각 하네스 스킬의 YAML 프론트매터에 직접 작성합니다.

**v1 (JSON 파일):**
```json
{
  "patterns": [
    {
      "regex": "useQuery|useMutation",
      "harness": "harness-fe-tanstack-query"
    }
  ]
}
```

**v2 (스킬 프론트매터):**
```yaml
---
name: harness-fe-tanstack-query
description: Use when working with TanStack Query — useQuery, useMutation...
user-invocable: true
matchPatterns:
  fileGlob: "^.*/src/.*\.(ts|tsx)$"
  regex:
    - "useQuery|useMutation|queryClient|useQueryClient"
---
```

matchPatterns가 없는 스킬은 description의 키워드로 자동 폴백 매칭됩니다.

## 프로젝트 고유 스크립트

v1에서 `claude-scripts/`에 프로젝트 고유 스크립트를 추가했다면, `migrate.sh`가 자동으로 `.claude/scripts/`로 이동합니다. sync.sh는 화이트리스트 외 파일을 무시하므로 안전합니다.

## 확인 방법

마이그레이션 후 다음을 확인하세요:

```bash
# 1. 훅 동작 확인 — 플랜 없이 편집 시도하면 차단되어야 함
claude
> "test" (Write 시도)

# 2. 하네스 제안 확인 — src/ 파일 읽기 시 제안이 나와야 함
> Read src/<any-file>.tsx

# 3. 구 경로 잔여 확인
grep -r 'claude-scripts/' .claude/settings.json
# → 출력이 없어야 정상
```
