#!/usr/bin/env python3
"""MCP server wrapping WebDeepSearch (DuckDuckGo deep web search).

Transport selection:
  - stdio (default): for local MCP clients (OpenCode, Claude Code, Cursor, ...)
  - streamable-http: for remote clients, endpoint /mcp

Configure via env vars or CLI flags:
  TRANSPORT (stdio|http), HOST (0.0.0.0), PORT (8000)
"""

import argparse
import asyncio
import os
from typing import Any, Dict, Optional

from mcp.server.mcpserver import MCPServer

from WebSearchAgent import WebDeepSearch, DEFAULT_CONFIG

SERVER_NAME = "web-deepsearch"
SERVER_VERSION = "1.0.0"

# Tool argument name -> WebDeepSearch config key
CONFIG_OVERRIDES = {
    "max_iterations": "max_iterations",
    "min_confidence": "min_confidence",
    "timeout": "timeout",
    "max_total_time": "max_total_time",
    "max_concurrent_fetches": "max_concurrent_fetches",
    "max_content_length": "max_content_length",
}

mcp = MCPServer(
    SERVER_NAME,
    version=SERVER_VERSION,
    instructions=(
        "DuckDuckGo-powered deep web search with iterative query refinement "
        "and full-page content extraction. Use web_deepsearch to search the "
        "web; results are returned as structured JSON."
    ),
)


@mcp.tool()
async def web_deepsearch(
    query: str,
    max_sources: int = 5,
    deep_search: bool = True,
    max_iterations: Optional[int] = None,
    min_confidence: Optional[float] = None,
    timeout: Optional[int] = None,
    max_total_time: Optional[int] = None,
    max_concurrent_fetches: Optional[int] = None,
    max_content_length: Optional[int] = None,
) -> Dict[str, Any]:
    """Search the web via DuckDuckGo with iterative deep-search refinement.

    Args:
        query: The search query.
        max_sources: Maximum sources to extract.
        deep_search: Enable iterative search refinement.
        max_iterations: Override max search iterations.
        min_confidence: Override minimum confidence (0..1) to stop refining.
        timeout: Override request timeout in seconds.
        max_total_time: Override total time budget in seconds.
        max_concurrent_fetches: Override concurrent page fetches.
        max_content_length: Override max extracted content length per source.
    """
    overrides = {
        "max_iterations": max_iterations,
        "min_confidence": min_confidence,
        "timeout": timeout,
        "max_total_time": max_total_time,
        "max_concurrent_fetches": max_concurrent_fetches,
        "max_content_length": max_content_length,
    }
    config = {k: v for k, v in overrides.items() if v is not None}

    agent = WebDeepSearch(config=config)
    # execute() internally calls asyncio.run() (aiohttp fast path), so it must
    # run in a worker thread when called from the MCP event loop.
    return await asyncio.to_thread(agent.execute, query, max_sources, deep_search)


@mcp.tool()
def web_deepsearch_server_info() -> Dict[str, Any]:
    """Return server capabilities, tool parameters and defaults (agent discovery)."""
    return {
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "transport": os.environ.get("TRANSPORT", "stdio"),
        "tools": {
            "web_deepsearch": {
                "query": {"type": "string", "required": True},
                "max_sources": {"type": "integer", "default": 5},
                "deep_search": {"type": "boolean", "default": True},
                "config_overrides": list(CONFIG_OVERRIDES.keys()),
            },
            "web_deepsearch_server_info": {},
        },
        "default_config": dict(DEFAULT_CONFIG),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WebDeepSearch MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.environ.get("TRANSPORT", "stdio"),
        help="MCP transport (default: TRANSPORT env or stdio)",
    )
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("PORT", "8000"))
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.transport == "http":
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            json_response=True,
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
