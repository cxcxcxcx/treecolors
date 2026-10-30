"""Fetchers for ArcGIS REST, Socrata and CSV tree inventories.

Every adapter writes the same normalized JSONL shape::

    {"lat": ..., "lng": ..., "raw": "...", "common": "...",
     "source": "...", "source_key": "...", "source_name": "...", "city": "..."}

The species/coordinate extraction is intentionally permissive because city
publishers use very different schemas.
"""

from __future__ import annotations

import csv
import io
import json
import time
from pathlib import Path
from typing import Any

import requests

from .cities import CitySpec, SourceSpec


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 tree-map-pipeline/1.0"
        )
    }
)


def _get_json(url: str, params: dict[str, Any], *, attempts: int = 4) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = SESSION.get(url, params=params, timeout=120)
            if response.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    response=response,
                )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError(f"ArcGIS/service error: {data['error']}")
            return data
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            sleep_for = 2 ** attempt
            print(f"    retry {attempt}/{attempts - 1} in {sleep_for}s: {exc}")
            time.sleep(sleep_for)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def fetch_domain_mapping(source: SourceSpec) -> dict[str, str]:
    """Return ``{common_name_code: scientific_name}`` from an ArcGIS domain."""

    if not source.domain_field:
        return {}
    metadata = _get_json(source.url, {"f": "json"})
    for field in metadata.get("fields", []):
        if field.get("name") != source.domain_field:
            continue
        domain = field.get("domain") or {}
        mapping: dict[str, str] = {}
        for coded in domain.get("codedValues") or []:
            code = coded.get("code")
            name = coded.get("name") or ""
            if code is None or not name:
                continue
            # Montgomery uses "Scientific,Common"; Ottawa uses just
            # "Scientific" with a separate common-name code.
            scientific = name.split(",", 1)[0].strip()
            if scientific and scientific.lower() != str(code).strip().lower():
                mapping[str(code)] = scientific
        return mapping
    return {}


def _first(props: dict[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = props.get(field)
        if value is None:
            continue
        text = str(value).replace("\xa0", " ").strip()
        if text and text.lower() not in {"nan", "none", "null"}:
            return text
    return None


def _invert_comma(name: str) -> str:
    if "," not in name:
        return name
    first, second = name.split(",", 1)
    first, second = first.strip(), second.strip()
    if first and second:
        return f"{second} {first}"
    return name


def _species_from_row(row: dict[str, Any], source: SourceSpec) -> str | None:
    if source.species_concat:
        parts = [str(row.get(field) or "").strip() for field in source.species_concat]
        raw = source.species_separator.join(part for part in parts if part)
    else:
        raw = _first(row, source.species_fields)
    if raw is None:
        return None
    if source.split_dash and " - " in raw:
        raw = raw.split(" - ", 1)[0].strip()
    if source.invert_comma:
        raw = _invert_comma(raw)
    return raw


def _point_from_value(value: Any) -> tuple[float, float] | None:
    """Parse a GeoJSON point object/string into ``(lat, lng)``."""

    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return None
    if not isinstance(value, dict):
        return None
    coordinates = value.get("coordinates")
    if not coordinates:
        return None
    # MultiPoint/LineString may nest one extra level.
    while isinstance(coordinates, (list, tuple)) and coordinates and isinstance(coordinates[0], (list, tuple)):
        coordinates = coordinates[0]
    if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
        try:
            return float(coordinates[1]), float(coordinates[0])
        except (TypeError, ValueError):
            return None
    return None


def _lat_lng(row: dict[str, Any], source: SourceSpec) -> tuple[float, float] | None:
    if "_lat" in row and "_lng" in row:
        try:
            return float(row["_lat"]), float(row["_lng"])
        except (TypeError, ValueError):
            pass
    if source.lat_field and source.lng_field:
        try:
            return float(row[source.lat_field]), float(row[source.lng_field])
        except (KeyError, TypeError, ValueError):
            pass
    if source.point_field:
        return _point_from_value(row.get(source.point_field))
    return None


def _write_record(
    handle: io.TextIOBase,
    row: dict[str, Any],
    source: SourceSpec,
    city: CitySpec,
) -> bool:
    raw = _species_from_row(row, source)
    if raw is None:
        return False
    point = _lat_lng(row, source)
    if point is None:
        return False
    lat, lng = point
    common = _first(row, source.common_fields)
    handle.write(
        json.dumps(
            {
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "raw": raw,
                "common": common,
                "source": source.slug,
                "source_key": f"{city.slug}:{source.slug}",
                "source_name": source.name,
                "city": source.fixed_city or city.name,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )
    return True


# --- ArcGIS ----------------------------------------------------------------
def _fetch_arcgis(city: CitySpec, source: SourceSpec, out_path: Path) -> int:
    domain_map = fetch_domain_mapping(source)
    if domain_map:
        print(f"    domain {source.domain_field}: {len(domain_map)} code -> scientific mappings")

    part_path = out_path.with_suffix(out_path.suffix + ".part")
    if part_path.exists():
        part_path.unlink()

    offset = 0
    written = 0
    page = 0
    with part_path.open("w", encoding="utf-8") as handle:
        while True:
            page += 1
            params = {
                "where": source.where,
                "outFields": ",".join(source.out_fields) or "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
                "resultOffset": offset,
                "resultRecordCount": source.page_size,
                "orderByFields": f"{source.id_field} ASC",
            }
            data = _get_json(f"{source.url.rstrip('/')}/query", params)
            features = data.get("features") or []
            if not features:
                break
            properties = data.get("properties") or {}
            exceeded = bool(properties.get("exceededTransferLimit") or data.get("exceededTransferLimit"))
            for feature in features:
                props = feature.get("properties") or {}
                geometry = feature.get("geometry") or {}
                coordinates = geometry.get("coordinates")
                if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
                    try:
                        row = {
                            **props,
                            "_lat": float(coordinates[1]),
                            "_lng": float(coordinates[0]),
                        }
                    except (TypeError, ValueError):
                        row = props
                else:
                    row = props
                if source.domain_field and row.get(source.species_fields[0]) in domain_map:
                    row[source.species_fields[0]] = domain_map[row[source.species_fields[0]]]
                if _write_record(handle, row, source, city):
                    written += 1
            offset += len(features)
            if page == 1 or page % 10 == 0:
                print(f"    page {page}: {written:,} rows")
            if len(features) < source.page_size and not exceeded:
                break
            time.sleep(0.05)
    part_path.replace(out_path)
    return written


# --- Socrata ---------------------------------------------------------------
def _fetch_socrata(city: CitySpec, source: SourceSpec, out_path: Path) -> int:
    part_path = out_path.with_suffix(out_path.suffix + ".part")
    if part_path.exists():
        part_path.unlink()

    offset = 0
    written = 0
    page = 0
    with part_path.open("w", encoding="utf-8") as handle:
        while True:
            page += 1
            params: dict[str, Any] = {
                "$limit": source.page_size,
                "$offset": offset,
            }
            if source.id_field:
                params["$order"] = source.id_field
            if source.where and source.where != "1=1":
                params["$where"] = source.where
            data = _get_json(source.url, params)
            rows = data if isinstance(data, list) else []
            if not rows:
                break
            for row in rows:
                if _write_record(handle, row, source, city):
                    written += 1
            offset += len(rows)
            if page == 1 or page % 5 == 0:
                print(f"    page {page}: {written:,} rows")
            if len(rows) < source.page_size:
                break
            time.sleep(0.05)
    part_path.replace(out_path)
    return written


# --- CSV -------------------------------------------------------------------
def _download(url: str, target: Path, *, referer: str = "") -> None:
    """Download a potentially large CSV to a local file with retries."""

    if target.exists() and target.stat().st_size > 0:
        return
    part = target.with_suffix(target.suffix + ".part")
    if part.exists():
        part.unlink()
    headers = {"Referer": referer} if referer else {}
    for attempt in range(1, 4):
        try:
            with SESSION.get(url, stream=True, timeout=300, headers=headers) as response:
                response.raise_for_status()
                with part.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        if chunk:
                            handle.write(chunk)
            part.replace(target)
            return
        except requests.RequestException as exc:
            if attempt == 3:
                raise
            print(f"    download retry {attempt}/2: {exc}")
            time.sleep(2 ** attempt)


def _fetch_csv(city: CitySpec, source: SourceSpec, out_path: Path) -> int:
    csv_path = out_path.with_suffix(".csv")
    _download(source.url, csv_path, referer=source.homepage or source.url)

    part_path = out_path.with_suffix(out_path.suffix + ".part")
    if part_path.exists():
        part_path.unlink()

    written = 0
    rows = 0
    with part_path.open("w", encoding="utf-8") as handle, csv_path.open(
        encoding=source.encoding, errors="replace", newline=""
    ) as text:
        reader = csv.DictReader(text, delimiter=source.delimiter)
        for row in reader:
            rows += 1
            if _write_record(handle, row, source, city):
                written += 1
            if rows % 50000 == 0:
                print(f"    rows {rows:,}: {written:,} usable")
    part_path.replace(out_path)
    print(f"    read {rows:,} CSV rows")
    return written


# --- Dispatch --------------------------------------------------------------
def fetch_source(city: CitySpec, source: SourceSpec, *, force: bool = False) -> int:
    raw_dir = RAW_ROOT / city.slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / f"{source.slug}.jsonl"

    if out_path.exists() and out_path.stat().st_size > 0 and not force:
        with out_path.open() as handle:
            count = sum(1 for _ in handle)
        print(f"  [skip] {city.slug}/{source.slug}: {count:,} cached rows")
        return count

    print(f"  [fetch:{source.kind}] {city.slug}/{source.slug}: {source.name}")
    if source.kind == "arcgis":
        written = _fetch_arcgis(city, source, out_path)
    elif source.kind == "socrata":
        written = _fetch_socrata(city, source, out_path)
    elif source.kind == "csv":
        written = _fetch_csv(city, source, out_path)
    else:
        raise SystemExit(f"Unknown source kind {source.kind!r}")

    print(f"  [done] {city.slug}/{source.slug}: {written:,} rows -> {out_path.relative_to(PROJECT_ROOT)}")
    return written


def fetch_city(city: CitySpec, *, force: bool = False) -> dict[str, int]:
    counts: dict[str, int] = {}
    for source in city.sources:
        counts[source.slug] = fetch_source(city, source, force=force)
    return counts


def raw_stats(city: CitySpec) -> dict[str, Any]:
    raw_dir = RAW_ROOT / city.slug
    stats: dict[str, Any] = {}
    for source in city.sources:
        path = raw_dir / f"{source.slug}.jsonl"
        stats[source.slug] = 0
        if path.exists():
            with path.open() as handle:
                stats[source.slug] = sum(1 for _ in handle)
    return stats
