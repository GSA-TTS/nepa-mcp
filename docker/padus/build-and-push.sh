#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" padus ghcr.io/gsa-tts/mcp-server-nepa-usgs-padus docker/Dockerfile
