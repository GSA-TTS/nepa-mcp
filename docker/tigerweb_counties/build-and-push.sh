#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/../build-image.sh" tigerweb_counties ghcr.io/gsa-tts/mcp-server-nepa-tigerweb-counties docker/Dockerfile
