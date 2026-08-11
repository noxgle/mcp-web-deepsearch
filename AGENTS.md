# AGENTS.md

## Purpose

Dockerized MCP server wrapping the upstream `WebSearchAgent.py` (DuckDuckGo
deep web search). Published to GHCR by CI as `ghcr.io/noxgle/mcp-web-deepsearch`
(`latest` + `sha-<short>` + semver tags). Any MCP client can consume it via
stdio (per-session container) or streamable HTTP (one shared container).

## File ownership — read this first

- `server/WebSearchAgent.py` — **vendored verbatim** from
  `github.com/noxgle/opencode-web-deepsearch` (MIT). NEVER hand-edit it.
  All wrapper logic lives in `server/mcp_server.py`.
- `server/mcp_server.py` — the only file with custom logic: `MCPServer`
  wrapper exposing exactly 2 tools (`web_deepsearch`,
  `web_deepsearch_server_info`) and the transport switch
  (`TRANSPORT=stdio|http`, `HOST`, `PORT` env or `--transport/--host/--port`).
- `Dockerfile` — `python:3.12-slim`, `ENTRYPOINT ["python", "server/mcp_server.py"]`,
  WORKDIR `/app`. `docker-compose.yml` runs the GHCR image (not a build) bound
  to `127.0.0.1:8000` deliberately — local-only, shared by many clients.

## Commands

```bash
docker build -t web-deepsearch-mcp .            # local build from source
docker compose pull && docker compose up -d     # run persistent HTTP server on 127.0.0.1:8000
docker run --rm -i ghcr.io/noxgle/mcp-web-deepsearch:latest   # stdio mode
```

There is no test suite. Verification is smoke-testing over JSON-RPC
(see Gotchas for the session header).

## Gotchas

- **Do not run `python server/mcp_server.py` on the host** — `mcp` is only
  installed inside the image. Test in Docker; the image contains the MCP
  client SDK, so a client script can be mounted and run in-container.
- MCP SDK v2 API (mcp>=1.12): `from mcp.server.mcpserver import MCPServer`;
  constructor takes `name`, `version=`, `instructions=`; transport options
  (`host`, `port`, `json_response`) go to `mcp.run()`, NOT the constructor.
- `WebDeepSearch.execute()` calls `asyncio.run()` internally. Async MCP tool
  handlers must wrap it in `asyncio.to_thread(...)` or they crash with
  RuntimeError (event loop already running).
- HTTP mode is **session-based**: the `initialize` response carries a
  `mcp-session-id` header; every later request must include it, otherwise the
  server answers `400 Bad Request: Missing session ID`. Raw `curl` tests must
  capture that header from the initialize response.
- Each `web_deepsearch` call creates a fresh `WebDeepSearch` instance
  (stateless); per-call config overrides (`max_iterations`, `min_confidence`,
  `timeout`, `max_total_time`, `max_concurrent_fetches`, `max_content_length`)
  are supported tool args.
- CI workflow (`.github/workflows/docker-publish.yml`) runs on push to `main`
  and `v*` tags, plus `workflow_dispatch`. After a server change, the runtime
  container must be refreshed with `docker compose pull && docker compose up -d`.
- The `gh` token for this account lacks `read:packages` — `gh api
  /user/packages/...` fails with 403. Verify GHCR visibility/pullability with
  plain `docker pull` instead (image is public).
- OpenCode integration (on this machine) is a global `"type": "remote"` MCP
  entry pointing at `http://127.0.0.1:8000/mcp`; config changes need an
  OpenCode restart (config is not hot-reloaded).