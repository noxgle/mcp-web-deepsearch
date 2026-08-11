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

## Quick install from GHCR

A ready-built image is published to GitHub Container Registry on every push to `main`:

```
ghcr.io/noxgle/mcp-web-deepsearch:latest
```

No Docker build required — just pull and run.

### stdio (local agents)

```bash
docker run --rm -i ghcr.io/noxgle/mcp-web-deepsearch:latest
```

Configure your local MCP client (e.g. OpenCode `opencode.json`):

```json
{
  "mcp": {
    "web-deepsearch": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/noxgle/mcp-web-deepsearch:latest"]
    }
  }
}
```

### streamable HTTP (remote agents)

One persistent container serves all MCP clients — recommended when running
multiple OpenCode instances (avoids spawning one Docker container per session):

```bash
docker compose pull && docker compose up -d
```

Endpoint (local only): `http://127.0.0.1:8000/mcp`

To update the image after a new release, run the same command again
(`docker compose pull` fetches the new `latest`).

```json
{
  "mcp": {
    "web-deepsearch": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

Additional tags on GHCR: `sha-<short>` for every commit and `v<version>` for git tags (e.g. `v1.0.0`).

## Config on other clients

The server works with any MCP client. Two options: **remote HTTP** (shared
persistent container — recommended) or **stdio** (the client spawns one
container per session). The remote HTTP option requires the persistent
container to be running (see Quick install from GHCR above).

### Claude Code

Remote (HTTP) — one command:

```bash
claude mcp add --transport http web-deepsearch http://127.0.0.1:8000/mcp
claude mcp list   # verify
```

Local (stdio):

```bash
claude mcp add --transport stdio web-deepsearch -- docker run --rm -i ghcr.io/noxgle/mcp-web-deepsearch:latest
```

Project-scoped `.mcp.json` (shared with the team):

```json
{
  "mcpServers": {
    "web-deepsearch": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global), then enable the
server in Cursor Settings → Tools & MCP:

```json
{
  "mcpServers": {
    "web-deepsearch": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Visual Studio Code

`.vscode/mcp.json` (workspace, commit to source control) or user profile
(`MCP: Open User Configuration` command). Note: VS Code uses the `servers`
key:

```json
{
  "servers": {
    "web-deepsearch": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

Stdio variant (no `-d` — the container must run in the foreground):

```json
{
  "servers": {
    "web-deepsearch": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/noxgle/mcp-web-deepsearch:latest"]
    }
  }
}
```

### Visual Studio (IDE)

`<SOLUTIONDIR>\.mcp.json` or `%USERPROFILE%\.mcp.json`, same `servers` format
as VS Code. Visual Studio also auto-discovers `.vscode/mcp.json` and
`.cursor/mcp.json`.

### Any other MCP client

Remote HTTP: point the client at the local endpoint
`http://127.0.0.1:8000/mcp` (no authentication required).

Stdio (works everywhere, one container per client session):

```json
{
  "mcpServers": {
    "web-deepsearch": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "ghcr.io/noxgle/mcp-web-deepsearch:latest"]
    }
  }
}
```

Claude Desktop only supports stdio — use the stdio form above or a proxy
(`npx mcp-remote http://127.0.0.1:8000/mcp --transport http-only`).

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
docker compose pull && docker compose up -d
# or:
docker run -d --name web-deepsearch -p 127.0.0.1:8000:8000 -e TRANSPORT=http ghcr.io/noxgle/mcp-web-deepsearch:latest
```

Endpoint (local only): `http://127.0.0.1:8000/mcp`

Example client config (HTTP MCP):

```json
{
  "mcp": {
    "web-deepsearch": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
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
