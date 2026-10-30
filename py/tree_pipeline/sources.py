"""ArcGIS REST source adapter and raw-data fetcher.

The fetcher is intentionally conservative:

* pages of 2,000 features (the usual ArcGIS maximum);
* ``outSR=4326`` so every source arrives in WGS84;
* retries with backoff on transient HTTP errors;
* writes JSONL to a ``.part`` file and only renames it on success, so an
  interrupted run never leaves a half-valid cache.
"""

from __future__ import annotations

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
                raise RuntimeError(f"ArcGIS error: {data['error']}")
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
    """Return ``{common_name_code: scientific_name}`` from a field domain.

    Montgomery's ``ITEM`` field is the motivating case: its coded values look
    like ``{"code": "Red Maple", "name": "Acer rubrum,Red Maple"}``.
    """

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
            scientific = name.split(",", 1)[0].strip()
            if scientific and scientific != name.strip():
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


def _feature_lat_lng(feature: dict[str, Any], props: dict[str, Any]) -> tuple[float, float] | None:
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
        try:
            lon, lat = float(coordinates[0]), float(coordinates[1])
            return lat, lon
        except (TypeError, ValueError):
            pass

    lat = props.get("LATITUDE", props.get("Latitude", props.get("lat")))
    lng = props.get("LONGITUDE", props.get("Longitude", props.get("lng")))
    if lat is not None and lng is not None:
        try:
            return float(lat), float(lng)
        except (TypeError, ValueError):
            return None
    return None


def fetch_source(city: CitySpec, source: SourceSpec, *, force: bool = False) -> int:
    raw_dir = RAW_ROOT / city.slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / f"{source.slug}.jsonl"

    if out_path.exists() and out_path.stat().st_size > 0 and not force:
        with out_path.open() as handle:
            count = sum(1 for _ in handle)
        print(f"  [skip] {city.slug}/{source.slug}: {count:,} cached rows")
        return count

    print(f"  [fetch] {city.slug}/{source.slug}: {source.name}")
    domain_map = fetch_domain_mapping(source)
    if domain_map:
        print(f"    domain {source.domain_field}: {len(domain_map)} code -> scientific mappings")

    part_path = out_path.with_suffix(out_path.suffix + ".part")
    if part_path.exists():
        part_path.unlink()

    offset = 0
    written = 0
    page = 0
    total_hint: int | None = None

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
            if total_hint is None:
                # Some servers include this only on the first page.
                total_hint = data.get("properties", {}).get("count")
            if not features:
                break

            for feature in features:
                props = feature.get("properties") or {}
                point = _feature_lat_lng(feature, props)
                if point is None:
                    continue
                lat, lng = point

                raw = _first(props, source.species_fields)
                if raw is None:
                    continue
                if source.domain_field and raw in domain_map:
                    raw = domain_map[raw]
                if source.split_dash and " - " in raw:
                    raw = raw.split(" - ", 1)[0].strip()
                if source.invert_comma:
                    raw = _invert_comma(raw)

                common = _first(props, source.common_fields)
                record = {
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "raw": raw,
                    "common": common,
                    "source": source.slug,
                    "source_name": source.name,
                    "city": source.fixed_city or city.name,
                }
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                written += 1

            offset += len(features)
            if page == 1 or page % 10 == 0:
                hint = f"/{total_hint:,}" if total_hint else ""
                print(f"    page {page}: {written:,}{hint} rows")
            if len(features) < source.page_size:
                break
            time.sleep(0.05)

    part_path.replace(out_path)
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
        if not path.exists():
            stats[source.slug] = 0
            continue
        with path.open() as handle:
            stats[source.slug] = sum(1 for _ in handle)
    return stats
