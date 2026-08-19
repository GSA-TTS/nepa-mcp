#!/usr/bin/env python3
"""HTTP entrypoint for hosting the FEMA NFHL MCP server as a containerized server.

This is an ADDITIVE wrapper — it does not modify any upstream server code. It
reuses the monorepo's own loader (``nepa_mcp.loader.load_server_module``) to
import the unmodified ``fema_nfhl/server.py`` and obtain its configured
``FastMCP`` instance, then:

  * registers a ``/health`` readiness endpoint, and
  * runs the server over streamable HTTP at ``:$PORT/mcp`` (default 8080)

instead of the stdio transport used for local MCP clients. Because tools are
imported from the upstream server module, upstream tool changes flow through
automatically after a ``git merge upstream/main`` — no edits here required.

The FEMA NFHL server needs no credentials — it queries the public FEMA National
Flood Hazard Layer ArcGIS services.

NOTE: this is the NEPA fork's FEMA NFHL server. Its image is published as
``mcp-server-nepa-fema-nfhl`` to disambiguate from the separate standalone
``mcp-server-fema-nfhl`` already in the hub catalog.

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

SERVER_NAME = "fema_nfhl"
# Image/DNS-safe form of the server name (no underscores) for the health label.
SERVICE_NAME = "mcp-server-nepa-fema-nfhl"


def build_app():
    """Load the unmodified FEMA NFHL server module and return its FastMCP instance."""
    # Load any optional credentials the way the stdio runtime does. FEMA NFHL
    # needs none (public FEMA ArcGIS services), but this keeps parity with
    # servers that do and is a no-op otherwise.
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
