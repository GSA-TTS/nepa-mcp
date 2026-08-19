# Container image for the FEMA NFHL (National Flood Hazard Layer) MCP server,
# hosted by the Obot MCP gateway as a `containerized` server. It serves MCP over
# streamable HTTP at :8080/mcp with a /health readiness endpoint (see
# docker/fema_nfhl/entry.py).
#
# NOTE: this is the NEPA fork's FEMA NFHL server. Its image is published as
# `mcp-server-nepa-fema-nfhl` to disambiguate from the separate standalone
# `mcp-server-fema-nfhl` already in the hub catalog.
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) because
# the FEMA NFHL server depends on the shared `nepa_mcp_common` package. Build
# with:
#     docker build -f docker/fema_nfhl/Dockerfile -t <image> .
# (see docker/fema_nfhl/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all 19 server directories to be present,
# which would mean copying the whole monorepo into every per-server image. Since
# we don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader (nepa_mcp.loader.load_server_module) searches
# `nepa_mcp/_servers/fema_nfhl` then `<repo-root>/fema_nfhl`, so
# /app/fema_nfhl/server.py resolves.
#
# FEMA NFHL queries the public FEMA National Flood Hazard Layer ArcGIS services;
# no credentials or secrets are needed or baked in.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the FEMA NFHL server's own requirements.txt
# (fastmcp, requests, shapely, uvicorn, starlette, sse-starlette) plus the
# shared runtime deps used by nepa_mcp_common / nepa_mcp (platformdirs,
# python-dotenv, pyproj). pyproj/shapely ship manylinux wheels so no system
# GEOS/PROJ build is required.
COPY fema_nfhl/requirements.txt ./fema_nfhl-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r fema_nfhl-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0" "python-dotenv>=1.1.0" "pyproj>=3.7.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what FEMA NFHL needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY fema_nfhl ./fema_nfhl
COPY docker/fema_nfhl/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
