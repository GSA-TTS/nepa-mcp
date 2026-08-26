# Container image for the EPA ACRES (Assessment, Cleanup and Redevelopment
# Exchange System) Brownfields MCP server, hosted by the Obot MCP gateway as a
# `containerized` server. It serves MCP over streamable HTTP at :8080/mcp with a
# /health readiness endpoint (see docker/epa_acres/entry.py).
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) because
# the EPA ACRES server depends on the shared `nepa_mcp_common` package. Build with:
#     docker build -f docker/epa_acres/Dockerfile -t <image> .
# (see docker/epa_acres/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all server directories to be present, which
# would mean copying the whole monorepo into every per-server image. Since we
# don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader (nepa_mcp.loader.load_server_module) searches
# `nepa_mcp/_servers/epa_acres` then `<repo-root>/epa_acres`, so
# /app/epa_acres/server.py resolves. The loader also inserts the server dir on
# sys.path so epa_acres/server.py's `from src.apis...` imports resolve.
#
# EPA ACRES queries the public EPA Envirofacts facility-points ArcGIS service;
# no credentials or secrets are needed or baked in.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the EPA ACRES server's own requirements.txt
# (fastmcp, requests, shapely, uvicorn, starlette, sse-starlette) plus the
# shared runtime deps used by nepa_mcp_common / nepa_mcp (platformdirs,
# python-dotenv, pyproj). pyproj/shapely ship manylinux wheels so no system
# GEOS/PROJ build is required.
COPY epa_acres/requirements.txt ./epa_acres-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r epa_acres-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0" "python-dotenv>=1.1.0" "pyproj>=3.7.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what EPA ACRES needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY epa_acres ./epa_acres
COPY docker/epa_acres/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
