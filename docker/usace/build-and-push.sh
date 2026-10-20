#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" usace ghcr.io/gsa-tts/mcp-server-nepa-usace docker/Dockerfile
