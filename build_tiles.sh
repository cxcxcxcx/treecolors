#!/usr/bin/env bash
# Build one vector tileset from every city GeoJSON.
#
# Adding a city does not require editing this file: drop its
# data/output/geojson/trees_<slug>.geojson in place and rerun.
set -euo pipefail
cd "$(dirname "$0")"

mapfile -t files < <(
  find data/output/geojson -maxdepth 1 -name 'trees_*.geojson' \
    ! -name 'trees_oakland.geojson' | sort
)

if [ "${#files[@]}" -eq 0 ]; then
  echo "No trees_*.geojson files found under data/output/geojson" >&2
  exit 1
fi

printf 'Building tiles from %d GeoJSON files:\n' "${#files[@]}"
printf '  %s\n' "${files[@]}"

tippecanoe --force \
  -o data/output/trees.mbtiles \
  -zg --drop-densest-as-needed \
  -l trees \
  "${files[@]}"

pmtiles convert data/output/trees.mbtiles web/trees.pmtiles
echo "Wrote web/trees.pmtiles"
