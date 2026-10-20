#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" cfr ghcr.io/gsa-tts/mcp-server-nepa-cfr docker/Dockerfile
