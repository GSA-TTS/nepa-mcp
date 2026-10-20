#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" gbif ghcr.io/gsa-tts/mcp-server-nepa-gbif docker/Dockerfile
