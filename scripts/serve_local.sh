#!/usr/bin/env bash
# Serve web/ locally with Range support (required by PMTiles).
#
# Usage: scripts/serve_local.sh [port]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8767}"

if ! command -v lighttpd >/dev/null 2>&1; then
  echo "lighttpd is required (python http.server does not support PMTiles Range requests)." >&2
  exit 1
fi

CONF="$(mktemp)"
trap 'rm -f "$CONF"' EXIT

cat >"$CONF" <<EOF
server.document-root = "$ROOT/web"
server.port = $PORT
server.bind = "127.0.0.1"
index-file.names = ( "index.html" )
mimetype.assign = (
  ".html" => "text/html",
  ".js" => "application/javascript",
  ".json" => "application/json",
  ".css" => "text/css",
  ".png" => "image/png",
  ".ico" => "image/x-icon",
  ".pmtiles" => "application/octet-stream",
  ".xml" => "application/xml",
  ".txt" => "text/plain"
)
EOF

echo "Serving $ROOT/web at http://127.0.0.1:$PORT/"
exec lighttpd -D -f "$CONF"
