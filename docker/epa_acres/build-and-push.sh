#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" epa_acres ghcr.io/gsa-tts/mcp-server-nepa-epa-acres docker/Dockerfile
