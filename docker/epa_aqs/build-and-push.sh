#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" epa_aqs ghcr.io/gsa-tts/mcp-server-nepa-epa-aqs docker/Dockerfile
