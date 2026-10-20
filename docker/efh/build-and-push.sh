#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" efh ghcr.io/gsa-tts/mcp-server-nepa-efh docker/Dockerfile
