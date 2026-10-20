#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" pcsrf ghcr.io/gsa-tts/mcp-server-nepa-noaa-pcsrf docker/Dockerfile
