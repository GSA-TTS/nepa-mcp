# Container image for the EPA AQS (Air Quality System) MCP server, hosted by the
# Obot MCP gateway as a `containerized` server. It serves MCP over streamable
# HTTP at :8080/mcp with a /health readiness endpoint (see docker/epa_aqs/entry.py).
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) because
# the EPA AQS server depends on the shared `nepa_mcp_common` package. Build with:
#     docker build -f docker/epa_aqs/Dockerfile -t <image> .
# (see docker/epa_aqs/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all 19 server directories to be present,
# which would mean copying the whole monorepo into every per-server image. Since
# we don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader (nepa_mcp.loader.load_server_module) searches
# `nepa_mcp/_servers/epa_aqs` then `<repo-root>/epa_aqs`, so /app/epa_aqs/server.py
# resolves.
#
# The EPA AQS server needs per-user credentials (EPA_AQS_EMAIL, EPA_AQS_API_KEY).
# They are NOT baked into the image; the gateway injects them at runtime
# (top-level `env` in the catalog entry).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the EPA AQS server's own requirements.txt
# (fastmcp, requests, shapely, uvicorn, starlette, sse-starlette) plus the
# shared runtime deps used by nepa_mcp_common / nepa_mcp (platformdirs,
# python-dotenv, pyproj). pyproj/shapely ship manylinux wheels so no system
# GEOS/PROJ build is required.
COPY epa_aqs/requirements.txt ./epa_aqs-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r epa_aqs-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0" "python-dotenv>=1.1.0" "pyproj>=3.7.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what EPA AQS needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY epa_aqs ./epa_aqs
COPY docker/epa_aqs/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
