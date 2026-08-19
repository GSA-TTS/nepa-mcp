# Container image for the CFR (Code of Federal Regulations) MCP server, hosted
# by the Obot MCP gateway as a `containerized` server. It serves MCP over
# streamable HTTP at :8080/mcp with a /health readiness endpoint (see
# docker/cfr/entry.py).
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) so the
# loader (nepa_mcp.loader.load_server_module) can resolve the server dir. Build
# with:
#     docker build -f docker/cfr/Dockerfile -t <image> .
# (see docker/cfr/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all 19 server directories to be present,
# which would mean copying the whole monorepo into every per-server image. Since
# we don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader searches `nepa_mcp/_servers/cfr` then
# `<repo-root>/cfr`, so /app/cfr/server.py resolves.
#
# CFR queries the public eCFR + Federal Register APIs; no credentials or secrets
# are needed or baked in. Unlike the geospatial servers, CFR needs no
# shapely/pyproj — only the small nepa_mcp runtime deps (platformdirs,
# python-dotenv).

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the CFR server's own requirements.txt
# (fastmcp, requests, httpx, pydantic, python-dotenv, uvicorn, starlette,
# sse-starlette) plus the shared runtime dep used by nepa_mcp.config
# (platformdirs).
COPY cfr/requirements.txt ./cfr-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r cfr-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what CFR needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY cfr ./cfr
COPY docker/cfr/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
