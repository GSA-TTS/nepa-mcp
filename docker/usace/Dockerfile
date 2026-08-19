# Container image for the USACE (U.S. Army Corps of Engineers regulatory /
# Section 404 jurisdiction) MCP server, hosted by the Obot MCP gateway as a
# `containerized` server. It serves MCP over streamable HTTP at :8080/mcp with a
# /health readiness endpoint (see docker/usace/entry.py).
#
# NOTE: this is the NEPA fork's USACE regulatory/jurisdiction server, distinct
# from the separate "USACE IWR River Mile Markers" entry already in the hub
# catalog. Its image is published as `mcp-server-nepa-usace`.
#
# Mirrors the pattern used by the other GSA MCP servers (e.g.
# mcp-server-regulations-gov, mcp-server-fema-nfhl): a plain pip install, PORT=8080
# selecting the HTTP transport, and a /health check. No BuildKit-only features,
# so it builds cleanly under `docker buildx --platform linux/amd64`.
#
# IMPORTANT: build context is the REPOSITORY ROOT (not this directory) because
# the USACE server depends on the shared `nepa_mcp_common` package. Build with:
#     docker build -f docker/usace/Dockerfile -t <image> .
# (see docker/usace/build-and-push.sh).
#
# We deliberately do NOT `pip install .` from the root pyproject.toml: its
# hatchling `force-include` requires all 19 server directories to be present,
# which would mean copying the whole monorepo into every per-server image. Since
# we don't want to edit upstream's pyproject.toml (keeps `git merge upstream`
# clean), we instead lay out the repo packages as siblings under /app and put
# /app on PYTHONPATH. The loader (nepa_mcp.loader.load_server_module) searches
# `nepa_mcp/_servers/usace` then `<repo-root>/usace`, so /app/usace/server.py
# resolves.
#
# USACE queries the public U.S. Army Corps of Engineers regulatory ArcGIS
# services; no credentials or secrets are needed or baked in.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

WORKDIR /app

# Runtime dependencies. These mirror the USACE server's own requirements.txt
# (fastmcp, requests, shapely, uvicorn, starlette, sse-starlette) plus the
# shared runtime deps used by nepa_mcp_common / nepa_mcp (platformdirs,
# python-dotenv, pyproj). pyproj/shapely ship manylinux wheels so no system
# GEOS/PROJ build is required.
COPY usace/requirements.txt ./usace-requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r usace-requirements.txt \
    && pip install --no-cache-dir "platformdirs>=4.0.0" "python-dotenv>=1.1.0" "pyproj>=3.7.0"

# Lay out the repo packages as siblings on PYTHONPATH. Only what USACE needs.
COPY nepa_mcp ./nepa_mcp
COPY nepa_mcp_common ./nepa_mcp_common
COPY usace ./usace
COPY docker/usace/entry.py ./entry.py

EXPOSE 8080

# PORT=8080 selects the streamable-HTTP transport at /mcp (see entry.py).
CMD ["sh", "-c", "PORT=8080 python /app/entry.py"]
