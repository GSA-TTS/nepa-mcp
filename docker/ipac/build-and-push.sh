#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" ipac ghcr.io/gsa-tts/mcp-server-nepa-ipac docker/Dockerfile
