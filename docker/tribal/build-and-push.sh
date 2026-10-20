#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" tribal ghcr.io/gsa-tts/mcp-server-nepa-tribal docker/Dockerfile
