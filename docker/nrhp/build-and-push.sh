#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" nrhp ghcr.io/gsa-tts/mcp-server-nepa-nrhp docker/Dockerfile
