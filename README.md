# web-deepsearch MCP Server

MCP (Model Context Protocol) server in Docker wrapping
[WebSearchAgent.py](https://github.com/noxgle/opencode-web-deepsearch) —
DuckDuckGo-powered deep web search with iterative query refinement and
full-page content extraction. No API key required.

The server is a standard MCP server, so **any MCP-capable agent** can use it:
OpenCode, Claude Code, Cursor, custom agents, etc. It supports both local
(stdio) and remote (streamable HTTP) clients and handles concurrent requests.

## Tools

| Tool | Description |
|------|-------------|
| `web_deepsearch` | Search the web. Args: `query` (required), `max_sources` (default 5), `deep_search` (default true), optional config overrides: `max_iterations`, `min_confidence`, `timeout`, `max_total_time`, `max_concurrent_fetches`, `max_content_length` |
| `web_deepsearch_server_info` | Return server capabilities, tool parameters and defaults (for agent discovery) |

## Build

```bash
docker build -t web-deepsearch-mcp .
```

## Usage

### stdio (local agents)

```bash
docker run --rm -i web-deepsearch-mcp
```

Configure your local MCP client (e.g. OpenCode `opencode.json`):

```json
{
  "mcp": {
    "web-deepsearch": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "web-deepsearch-mcp"]
    }
  }
}
```

### streamable HTTP (remote agents)

```bash
docker compose up -d
# or:
docker run -d --name web-deepsearch -p 8000:8000 -e TRANSPORT=http web-deepsearch-mcp
```

Endpoint: `http://<host>:8000/mcp`

Example client config (HTTP MCP):

```json
{
  "mcp": {
    "web-deepsearch": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## Output format

`web_deepsearch` returns structured JSON:

```json
{
  "query": "TypeScript 5.x features",
  "sources": [
    {
      "title": "TypeScript 5.0 - Major Changes",
      "url": "https://example.com/typescript-5",
      "snippet": "TypeScript 5.0 brings...",
      "content": "Full extracted content...",
      "domain": "example.com"
    }
  ],
  "iterations_used": 3,
  "source_count": 5,
  "domain_count": 3,
  "errors": {},
  "skipped_urls": {},
  "fetch_stats": {
    "attempted": 5,
    "succeeded": 5,
    "failed": 0,
    "non_html": 0
  }
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSPORT` | `stdio` | `stdio` or `http` (streamable-http) |
| `HOST` | `0.0.0.0` | Bind address (HTTP mode) |
| `PORT` | `8000` | Listen port (HTTP mode) |

## Notes

- The container requires outbound internet access (DuckDuckGo + page fetches).
- DuckDuckGo may rate-limit; deep search runs multiple iterations and retries.
- `server/WebSearchAgent.py` is vendored verbatim from
  <https://github.com/noxgle/opencode-web-deepsearch> (MIT license); all
  wrapper logic lives in `server/mcp_server.py`.
