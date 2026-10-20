#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" blm ghcr.io/gsa-tts/mcp-server-nepa-blm docker/Dockerfile
