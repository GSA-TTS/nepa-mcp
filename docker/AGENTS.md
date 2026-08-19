# Containerizing nepa-mcp servers for the Obot MCP gateway

This directory holds the **additive** containerization layer for the nepa-mcp
servers. It lets each stdio server be hosted by the GSA Obot MCP gateway as a
`containerized` server over streamable HTTP, **without modifying any upstream
(pnnl) code** — so `git merge upstream/main` stays conflict-free.

Each server gets its own `docker/<server>/` subdirectory. `blm/` is the
reference implementation; copy it when adding a new server.

## Why additive (do NOT edit upstream files)

This repo is a fork of `pnnl/nepa-mcp` and we want to keep pulling upstream
updates:

```sh
git remote add upstream https://github.com/pnnl/nepa-mcp.git   # one-time
git fetch upstream
git merge upstream/main
```

To keep merges clean, **never edit `<server>/server.py`, the root
`pyproject.toml`, or anything else upstream owns.** All container-specific code
lives here under `docker/`. The HTTP shim imports the *unmodified* upstream
server module and swaps only the transport.

## Image naming convention

Going forward, images for these NEPA-related servers use the naming convention:

```
ghcr.io/gsa-tts/mcp-server-nepa-<agency>
```

e.g. `mcp-server-nepa-blm`, `mcp-server-nepa-census`, `mcp-server-nepa-fema-nfhl`.
The `nepa-` prefix scopes them to this fork and disambiguates from unrelated
GSA MCP servers (e.g. the standalone `mcp-server-fema-nfhl`).

> **Existing exceptions:** the first two images were published before this
> convention as `mcp-server-blm` and `mcp-server-census` (no `nepa-` prefix).
> Leave them as-is unless/until they are re-published under the new name; new
> servers should use `mcp-server-nepa-<agency>`.

## Catalog display-name convention

Going forward, the catalog `name` (the server's display name in the gateway)
uses the form:

```
NEPA <AGENCY>
```

e.g. `NEPA CFR`, `NEPA BLM`, `NEPA Census`. This groups the NEPA servers
together in the gateway UI and disambiguates them from unrelated GSA servers.
This applies to the `name:` field in the catalog entry (`<server>.yaml`) in
`GSA-TTS/mcp-server-hub-catalog`.

> **Existing exceptions:** the first entries were added before this convention
> with plain names (`BLM`, `Census`, `CFR`). Do not apply retroactively; use
> `NEPA <AGENCY>` for new catalog entries only.

## Per-server layout

```
docker/<server>/
├── entry.py           # HTTP shim: import upstream server, add /health, run http transport
├── Dockerfile         # build recipe (context = repo root)
├── .dockerignore      # trim build context
└── build-and-push.sh  # build + push ghcr.io/gsa-tts/mcp-server-nepa-<agency>
```

## How the pieces fit

- **`entry.py`** reuses the monorepo's own loader,
  `nepa_mcp.loader.load_server_module("<server>")`, to import the unmodified
  `<server>/server.py` and grab its configured `FastMCP` instance (`module.mcp`).
  It then:
  - registers a `/health` route (`@mcp.custom_route("/health", ...)`), and
  - runs `mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT","8080")), path="/mcp")`.

  Because the tools come from the upstream module, upstream tool changes flow
  through automatically after a merge — no edits to `entry.py` needed.

- **`Dockerfile`** uses `python:3.12-slim` (the repo requires >=3.12) and lays
  out `nepa_mcp`, `nepa_mcp_common`, and the server dir as siblings under
  `/app` with `PYTHONPATH=/app`. We deliberately do **not** `pip install .`
  from the root `pyproject.toml`: its hatchling `force-include` requires *all*
  19 server directories to be present, which would force copying the whole
  monorepo into every image. Laying out only the needed packages avoids that
  and avoids editing the upstream `pyproject.toml`.

  Dependencies are installed from `<server>/requirements.txt` plus the shared
  runtime deps used by `nepa_mcp` / `nepa_mcp_common` (`platformdirs`,
  `python-dotenv`, `pyproj`). `shapely`/`pyproj` ship manylinux wheels, so no
  system GEOS/PROJ build is required.

- The gateway EC2 host is **x86_64**, so images MUST be built `linux/amd64`
  (buildx handles emulation from Apple Silicon). An arm64-only image makes the
  gateway fail with a misleading `No such image ...` error.

## Adding a new server (checklist)

1. `cp -r docker/blm docker/<server>` and update:
   - `entry.py`: set `SERVER_NAME = "<server>"`.
   - `Dockerfile`: copy `<server>/requirements.txt` and the `<server>` dir;
     adjust the extra shared deps only if that server needs more.
   - `build-and-push.sh`: set `IMAGE=ghcr.io/gsa-tts/mcp-server-nepa-<agency>`
     and `DOCKERFILE=docker/<server>/Dockerfile`.
2. Build locally and verify (see below).
3. Publish: `bash docker/<server>/build-and-push.sh`, then set the GHCR package
   visibility to **Public** (the gateway's Docker backend pulls without auth).
4. Add the catalog entry in `GSA-TTS/mcp-server-hub-catalog` (`<server>.yaml`,
   `docs/servers/<server>.md`, `icons/<server>.png`, README row). `repoURL`
   points at `https://github.com/GSA-TTS/nepa-mcp` for every server.

### Servers that need per-user credentials

Most servers wrap public, keyless APIs → catalog `serverUserType: multiUser`,
no `env`. Two need per-user credentials and should be `singleUser` with a
**top-level** `env` list in the catalog entry (not nested under
`containerizedConfig`):

- `census` → `CENSUS_API_KEY`
- `epa_aqs` → `EPA_AQS_EMAIL`, `EPA_AQS_API_KEY`

The gateway injects these into the container at runtime; `load_credentials()`
in `entry.py` is a no-op for keyless servers and picks up env-provided values
for these.

## Build & verify locally

```sh
# Local single-arch build (loads into docker, no push):
PUSH=0 bash docker/<server>/build-and-push.sh

# Run and smoke-test:
docker run --rm -p 8080:8080 ghcr.io/gsa-tts/mcp-server-nepa-<agency>:0.1.0
curl -s localhost:8080/health          # -> {"status":"healthy",...}
```

MCP handshake (streamable HTTP requires the session-id dance):

```sh
# 1) initialize — capture the mcp-session-id response header
SID=$(curl -s -X POST localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}' \
  -D - -o /dev/null | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r')

# 2) send the initialized notification
curl -s -X POST localhost:8080/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null

# 3) list tools
curl -s -X POST localhost:8080/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

> Note: a `tools/call` that hits an upstream ArcGIS service needs outbound
> internet. In a sandbox without egress it will fail on DNS resolution — that
> still confirms the server path is wired up correctly.

## Publish notes

- Image tags: `ghcr.io/gsa-tts/mcp-server-nepa-<agency>:<version>` + `:latest`.
  Version defaults to `0.1.0`; override with `VERSION=x.y.z`.
- First push per image: set GHCR package visibility to **Public**.
- Confirm architecture: `docker manifest inspect <image>:<version> | grep architecture`
  (must be `amd64`).
- No secrets are baked into images; per-user credentials are injected at runtime
  by the gateway.
