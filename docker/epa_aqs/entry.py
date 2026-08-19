#!/usr/bin/env python3
"""HTTP entrypoint for hosting the EPA AQS MCP server as a containerized server.

This is an ADDITIVE wrapper — it does not modify any upstream server code. It
reuses the monorepo's own loader (``nepa_mcp.loader.load_server_module``) to
import the unmodified ``epa_aqs/server.py`` and obtain its configured
``FastMCP`` instance, then:

  * registers a ``/health`` readiness endpoint, and
  * runs the server over streamable HTTP at ``:$PORT/mcp`` (default 8080)

instead of the stdio transport used for local MCP clients. Because tools are
imported from the upstream server module, upstream tool changes flow through
automatically after a ``git merge upstream/main`` — no edits here required.

The EPA AQS server needs per-user credentials (EPA_AQS_EMAIL and
EPA_AQS_API_KEY); the gateway injects them into the container at runtime (see
the catalog entry's top-level ``env``). ``load_credentials()`` picks up the
env-provided values.

Mirrors the container pattern used by the other GSA MCP servers
(e.g. mcp-server-regulations-gov, mcp-server-fema-nfhl): PORT=8080 selects the
HTTP transport at /mcp with a /health check.
"""

from __future__ import annotations

import os

from starlette.requests import Request
from starlette.responses import JSONResponse

from nepa_mcp.config import load_credentials
from nepa_mcp.loader import load_server_module

SERVER_NAME = "epa_aqs"
# Image/DNS-safe form of the server name (no underscores) for the health label.
SERVICE_NAME = "mcp-server-nepa-epa-aqs"


def build_app():
    """Load the unmodified EPA AQS server module and return its FastMCP instance."""
    # Load optional credentials the way the stdio runtime does. For epa_aqs this
    # picks up EPA_AQS_EMAIL and EPA_AQS_API_KEY from the environment (injected
    # by the gateway).
    load_credentials()

    module = load_server_module(SERVER_NAME)
    mcp = module.mcp

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy", "service": SERVICE_NAME})

    return mcp


def main() -> None:
    mcp = build_app()
    port = int(os.getenv("PORT", "8080"))
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
        show_banner=False,
    )


if __name__ == "__main__":
    main()
