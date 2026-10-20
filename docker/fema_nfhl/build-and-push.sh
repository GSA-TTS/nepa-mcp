#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" fema_nfhl ghcr.io/gsa-tts/mcp-server-nepa-fema-nfhl docker/Dockerfile
