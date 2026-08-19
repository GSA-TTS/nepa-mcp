# Container image for the TIGERweb Counties MCP server (Census TIGERweb county
# discovery), hosted by the Obot MCP gateway as a `containerized` server. It
# serves MCP over streamable HTTP at :8080/mcp with a /health readiness endpoint
# (see docker/tigerweb_counties/entry.py).
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) because
# the server depends on the shared `nepa_mcp_common` package. Build with:
#     docker build -f docker/tigerweb_counties/Dockerfile -t <image> .
# (see docker/tigerweb_counties/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all 19 server directories to be present,
# which would mean copying the whole monorepo into every per-server image. Since
# we don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader (nepa_mcp.loader.load_server_module) searches
# `nepa_mcp/_servers/tigerweb_counties` then `<repo-root>/tigerweb_counties`, so
# /app/tigerweb_counties/server.py resolves.
#
# TIGERweb Counties queries the public Census TIGERweb ArcGIS service; no
# credentials or secrets are needed or baked in.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the server's own requirements.txt (fastmcp,
# requests, shapely, uvicorn, starlette, sse-starlette) plus the shared runtime
# deps used by nepa_mcp_common / nepa_mcp (platformdirs, python-dotenv, pyproj).
# pyproj/shapely ship manylinux wheels so no system GEOS/PROJ build is required.
COPY tigerweb_counties/requirements.txt ./tigerweb_counties-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r tigerweb_counties-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0" "python-dotenv>=1.1.0" "pyproj>=3.7.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what the server needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY tigerweb_counties ./tigerweb_counties
COPY docker/tigerweb_counties/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
