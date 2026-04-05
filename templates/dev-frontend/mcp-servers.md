# MCP Servers — dev-frontend

## 필수

```bash
# 라이브러리 문서 참조 (React, TanStack Query 등)
claude mcp add context7 -- npx -y @upstash/context7-mcp
```

## 권장

```bash
# 브라우저 자동화 (E2E 테스트, 시각 검증)
claude mcp add playwright -- npx -y @playwright/mcp@latest

# 구조화된 사고 (복잡한 설계 결정)
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

## 선택

```bash
# Chrome DevTools (라이브 디버깅 — Playwright와 동시 사용 불가)
claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp

# 웹 검색 (기술 조사)
claude mcp add tavily-mcp -- npx -y tavily-mcp

# Figma 디자인 연동
# Claude Code 설정에서 figma 플러그인 활성화

# Notion 문서 관리
claude mcp add notion -- npx -y @notionhq/notion-mcp-server
```

## 참고

- Playwright와 chrome-devtools는 동시에 사용할 수 없습니다. 하나만 활성화하세요.
- chrome-devtools 사용 시 로그인이 필요하면:
  ```bash
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/.chrome-debug-profile"
  ```
