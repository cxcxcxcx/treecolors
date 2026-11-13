#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Keep deployment credentials/endpoints out of git.
if [ -f .deploy.env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.deploy.env
  set +a
fi

: "${DEPLOY_HOST:?Set DEPLOY_HOST in .deploy.env or the environment}"
: "${DEPLOY_PATH:?Set DEPLOY_PATH in .deploy.env or the environment}"

NEW_VERSION="tree-map-v$(date +%Y%m%d-%H%M%S)"
sed -i "s/const CACHE_NAME = .*/const CACHE_NAME = '$NEW_VERSION';/" web/sw.js
# Also change the SW registration URL so a stale CDN copy is never reused.
sed -i "s/const SW_QUERY = '[^']*';/const SW_QUERY = '$NEW_VERSION';/" web/index.html
echo "Updated sw.js cache to $NEW_VERSION"

# web/preview is scratch space for reviews; it must never reach production.
rsync -avz --delete --exclude 'preview/' web/ "$DEPLOY_HOST:$DEPLOY_PATH"
