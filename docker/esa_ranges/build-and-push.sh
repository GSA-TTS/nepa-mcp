#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" esa_ranges ghcr.io/gsa-tts/mcp-server-nepa-esa-ranges docker/Dockerfile
