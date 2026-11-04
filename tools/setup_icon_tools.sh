#!/usr/bin/env bash
# Recreate the tooling needed by scripts/build_icon_flower.py.
#
# vtracer ships a cp314 wheel that segfaults on some inputs, so the icon
# pipeline pins Python 3.12 in a local venv (git-ignored). Everything else is
# a normal system tool.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required (https://docs.astral.sh/uv/)" >&2
  exit 1
fi
for tool in rsvg-convert potrace; do
  command -v "$tool" >/dev/null 2>&1 || { echo "missing $tool" >&2; exit 1; }
done

uv venv --python 3.12 tools/venv-vtrace
uv pip install --python tools/venv-vtrace/bin/python vtracer
tools/venv-vtrace/bin/python -c "import vtracer; print('vtracer ready')"
