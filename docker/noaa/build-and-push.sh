#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" noaa ghcr.io/gsa-tts/mcp-server-nepa-noaa docker/Dockerfile
