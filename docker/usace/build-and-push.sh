#!/bin/bash
# Build the USACE MCP server container image and push it to GHCR.
#
# The image is consumed by the Obot MCP gateway as a hosted "containerized" MCP
# server (see the mcp-server-hub-catalog entry usace.yaml). It serves MCP over
# streamable HTTP at :8080/mcp with a health check at :8080/health.
#
# This is additive to the upstream (pnnl) monorepo: it builds from the additive
# docker/usace/entry.py HTTP shim + the usace server dir, without modifying any
# upstream server code, so `git merge upstream/main` stays conflict-free.
#
# NOTE: this is the NEPA fork's USACE regulatory/jurisdiction server, distinct
# from the separate "USACE IWR River Mile Markers" (obot-usace-iwr) entry
# already in the hub catalog. The image is mcp-server-nepa-usace.
#
# Prerequisites:
#   - docker with buildx (for --platform)
#   - Authenticated to GHCR:
#       echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
#     (token needs write:packages scope)
#
# Usage:
#   bash docker/usace/build-and-push.sh            # build + push :<version> and :latest
#   PUSH=0 bash docker/usace/build-and-push.sh     # local build only (loads into docker)
#
# The gateway EC2 host is x86_64, so we build linux/amd64 (even from an arm64
# Apple Silicon workstation — buildx handles the emulation). An arm64-only image
# makes the gateway fail with a misleading "No such image ..." error.
#
# This script bakes NO secrets into the image; USACE needs no credentials.
set -euo pipefail

# Repo root is two levels up from docker/usace/.
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

REGISTRY="ghcr.io"
# NEPA server image naming convention: mcp-server-nepa-<agency> (see docker/AGENTS.md).
IMAGE="${REGISTRY}/gsa-tts/mcp-server-nepa-usace"
DOCKERFILE="docker/usace/Dockerfile"

# Version tag. Independent of the monorepo package version so USACE image
# releases can be cut on their own cadence. Override with VERSION=x.y.z.
VERSION="${VERSION:-0.1.0}"

PUSH="${PUSH:-1}"

if [[ "$PUSH" == "1" ]]; then
  echo "=== Building + pushing ${IMAGE}:${VERSION} and :latest (linux/amd64) ==="
  docker buildx build \
    --platform linux/amd64 \
    -f "$DOCKERFILE" \
    -t "${IMAGE}:${VERSION}" \
    -t "${IMAGE}:latest" \
    --push \
    .
  echo ""
  echo "Pushed:"
  echo "  ${IMAGE}:${VERSION}"
  echo "  ${IMAGE}:latest"
  echo ""
  echo "NOTE: On first push, set the GHCR package visibility to PUBLIC so the"
  echo "Obot docker runtime backend (which has no image-pull auth) can pull it:"
  echo "  GitHub -> Org packages -> mcp-server-nepa-usace -> Package settings"
  echo "  -> Change visibility -> Public"
  echo ""
  echo "Verify the published architecture is amd64:"
  echo "  docker manifest inspect ${IMAGE}:${VERSION} | grep architecture"
else
  echo "=== Building ${IMAGE}:${VERSION} locally (PUSH=0, single-arch, loaded into docker) ==="
  docker buildx build \
    -f "$DOCKERFILE" \
    -t "${IMAGE}:${VERSION}" \
    -t "${IMAGE}:latest" \
    --load \
    .
  echo ""
  echo "Built locally: ${IMAGE}:${VERSION}"
  echo "Test it:"
  echo "  docker run --rm -p 8080:8080 ${IMAGE}:${VERSION}"
  echo "  curl -s localhost:8080/health"
fi
