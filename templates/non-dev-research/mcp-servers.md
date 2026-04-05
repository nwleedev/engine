# MCP Servers — non-dev-research

## 필수

```bash
# 웹 검색/크롤링 (리서치 핵심 도구)
claude mcp add tavily-mcp -- npx -y tavily-mcp
```

## 권장

```bash
# 구조화된 사고 (복잡한 분석, MECE 분해)
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# Notion 연동 (리서치 결과 정리)
claude mcp add notion -- npx -y @notionhq/notion-mcp-server
```

## 선택

```bash
# 라이브러리/프레임워크 문서 (기술 리서치 시)
claude mcp add context7 -- npx -y @upstash/context7-mcp
```
