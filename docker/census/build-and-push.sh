#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" census ghcr.io/gsa-tts/mcp-server-nepa-census docker/Dockerfile
