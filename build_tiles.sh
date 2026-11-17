#!/usr/bin/env bash
# Build one vector tileset from every city GeoJSON.
#
# The data set is large enough that a single tippecanoe run can be memory
# hungry, so cities are tiled in small batches and merged with tile-join.
set -euo pipefail
cd "$(dirname "$0")"

BATCH_DIR="data/output/batches"
rm -rf "$BATCH_DIR"
mkdir -p "$BATCH_DIR"

# tippecanoe spills its external sort to $TMPDIR.  Left unset that is /tmp,
# which on this machine is a tmpfs — i.e. RAM — and a build that kills itself
# when the inputs get large.  Keep the scratch on the project disk.
export TMPDIR="${TMPDIR:-$PWD/data/output/tmp}"
mkdir -p "$TMPDIR"

# Batch by cumulative input size, not by file count: four medium cities are
# fine, but two 250 MB ones expanded in memory are not.  A single file larger
# than the cap still gets a batch to itself.
BATCH_BYTES=$((400 * 1024 * 1024))

# ``trees_oakland.geojson`` is the superseded 2013 export whose rows all share
# one placeholder coordinate.  The current Oakland inventory is
# ``trees_oakland_ca.geojson`` and tiles normally.
mapfile -t files < <(
  find data/output/geojson -maxdepth 1 -name 'trees_*.geojson' \
    ! -name 'trees_oakland.geojson' | sort
)

if [ "${#files[@]}" -eq 0 ]; then
  echo "No trees_*.geojson files found under data/output/geojson" >&2
  exit 1
fi

printf 'Building tiles from %d GeoJSON files in batches:\n' "${#files[@]}"
batch=()
batch_bytes=0
batch_no=0
flush_batch() {
  if [ "${#batch[@]}" -eq 0 ]; then
    return
  fi
  batch_no=$((batch_no + 1))
  out="$BATCH_DIR/batch_$(printf '%02d' "$batch_no").mbtiles"
  echo "  batch $batch_no: ${#batch[@]} files, $((batch_bytes / 1024 / 1024)) MB -> $out"
  tippecanoe --force -o "$out" -z 12 --drop-densest-as-needed \
    --maximum-tile-bytes=1500000 -l trees "${batch[@]}"
  batch=()
  batch_bytes=0
}

for file in "${files[@]}"; do
  size=$(stat -c %s "$file")
  if [ "${#batch[@]}" -gt 0 ] && [ $((batch_bytes + size)) -gt "$BATCH_BYTES" ]; then
    flush_batch
  fi
  batch+=("$file")
  batch_bytes=$((batch_bytes + size))
done
flush_batch

mapfile -t batch_files < <(find "$BATCH_DIR" -name 'batch_*.mbtiles' | sort)
echo "Merging ${#batch_files[@]} batches with tile-join ..."
tile-join --force --no-tile-size-limit -o data/output/trees.mbtiles "${batch_files[@]}"

pmtiles convert data/output/trees.mbtiles web/trees.pmtiles
echo "Wrote web/trees.pmtiles"
