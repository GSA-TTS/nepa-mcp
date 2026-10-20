#!/bin/bash
set -euo pipefail

if [[ "$#" -ne 3 ]]; then
  printf 'Usage: %s <server> <image> <dockerfile>\n' "$0" >&2
  exit 2
fi

SERVER="$1"
IMAGE="$2"
DOCKERFILE="$3"
VERSION="${VERSION:-0.1.6}"
PUSH="${PUSH:-0}"
PUBLISH_LATEST="${PUBLISH_LATEST:-0}"

case "$PUSH" in
  0|1) ;;
  *) printf 'PUSH must be 0 or 1, got %q\n' "$PUSH" >&2; exit 2 ;;
esac
case "$PUBLISH_LATEST" in
  0|1) ;;
  *) printf 'PUBLISH_LATEST must be 0 or 1, got %q\n' "$PUBLISH_LATEST" >&2; exit 2 ;;
esac
if [[ "$PUBLISH_LATEST" == "1" && "$PUSH" != "1" ]]; then
  printf 'PUBLISH_LATEST=1 requires PUSH=1\n' >&2
  exit 2
fi
if [[ ! "$VERSION" =~ ^[0-9A-Za-z][0-9A-Za-z._-]*$ ]]; then
  printf 'VERSION is not a valid container tag: %q\n' "$VERSION" >&2
  exit 2
fi

case "$SERVER" in
  blm|census|cfr|efh|epa_acres|epa_aqs|esa_ranges|fema_nfhl|gbif|ipac|noaa|nrhp|padus|pcsrf|tigerweb_counties|tribal|usace) ;;
  *) printf 'Unsupported container server: %q\n' "$SERVER" >&2; exit 2 ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

REVISION="$(git rev-parse HEAD)"
CREATED="$(git show -s --format=%cI HEAD)"
SOURCE_DIRTY=0
if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  SOURCE_DIRTY=1
fi
if [[ "$PUSH" == "1" && "$SOURCE_DIRTY" == "1" ]]; then
  printf 'Refusing to publish from a dirty worktree; commit and review all image inputs first.\n' >&2
  exit 2
fi
BUILD_ARGS=(
  --platform linux/amd64
  -f "$DOCKERFILE"
  -t "${IMAGE}:${VERSION}"
  --build-arg "VERSION=${VERSION}"
  --build-arg "REVISION=${REVISION}"
  --build-arg "CREATED=${CREATED}"
  --build-arg "SERVER=${SERVER}"
  --build-arg "IMAGE_TITLE=${IMAGE##*/}"
  --build-arg "SOURCE_DIRTY=${SOURCE_DIRTY}"
)

if [[ "$PUBLISH_LATEST" == "1" ]]; then
  BUILD_ARGS+=(-t "${IMAGE}:latest")
fi

if [[ "$PUSH" == "1" ]]; then
  printf 'Building and pushing %s:%s for linux/amd64\n' "$IMAGE" "$VERSION"
  docker buildx build "${BUILD_ARGS[@]}" --push .
  printf 'Published immutable deployment candidate: %s:%s\n' "$IMAGE" "$VERSION"
else
  printf 'Building %s:%s locally for linux/amd64 (no push)\n' "$IMAGE" "$VERSION"
  docker buildx build "${BUILD_ARGS[@]}" --load .
  printf 'Built locally. Run: docker run --rm --platform linux/amd64 -e PORT=8080 -p 8080:8080 %s:%s\n' "$IMAGE" "$VERSION"
fi

printf 'Server: %s\nRevision: %s\nSource dirty: %s\nCreated: %s\n' "$SERVER" "$REVISION" "$SOURCE_DIRTY" "$CREATED"
