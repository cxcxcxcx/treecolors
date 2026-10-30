"""Fill missing species in the knowledge base with a batched LLM pass.

This is intentionally offline: the model is only asked to resolve names and
describe species traits.  It never sees tree coordinates and never predicts
where a tree is.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .cities import CitySpec
from .species import (
    DEFAULT_ALIASES,
    DEFAULT_KB,
    SpeciesResolver,
    is_invalid,
    norm_key,
)
from .sources import RAW_ROOT


BATCH_SIZE = 20

_PROMPT = """You are resolving tree names from North American city tree inventories.

Input: a JSON array of tree names. They may be scientific names, common names,
cultivars, synonyms, typos, or genus-level names.

Return ONE JSON object keyed by the EXACT input string. For each input, return:
{
  "scientific_name": "Genus species" or "Genus spp.",
  "common_names": ["..."],
  "deciduous": true or false,
  "fall_colors": true or false,
  "beautiful_flowers": true or false,
  "blooming_season": "Spring" or "N/A",
  "chinese_common_names": ["..."],
  "explanation": "one short sentence"
}

Rules:
- Resolve typos, synonyms, and cultivar names to the accepted scientific name.
- For a genus-level input, use "Genus spp." and give genus-level traits.
- Do not invent a species when uncertain; use the closest accepted name and say so in the explanation.
- Keep explanations short and factual.
"""


def _try_resolve(resolver: SpeciesResolver, value: str):
    if not value:
        return None
    hit = resolver.resolve(value)
    if hit is not None:
        return hit
    if "," in value:
        first, second = value.split(",", 1)
        inverted = f"{second.strip()} {first.strip()}"
        return resolver.resolve(inverted)
    return None


def _read_unresolved(cities: list[CitySpec], resolver: SpeciesResolver) -> Counter[str]:
    unresolved: Counter[str] = Counter()
    for city in cities:
        for source in city.sources:
            path = RAW_ROOT / city.slug / f"{source.slug}.jsonl"
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    raw = str(record.get("raw") or "").strip()
                    common = str(record.get("common") or "").strip()
                    candidate = raw or common
                    if raw and common and common != raw and _try_resolve(resolver, raw) is None:
                        # Prefer a human-readable common name for code-only
                        # inventories (Mississauga BOTNAME/BOTDESC).
                        candidate = common
                    if not candidate or len(candidate) > 120:
                        continue
                    if is_invalid(candidate):
                        continue
                    if _try_resolve(resolver, candidate) is None:
                        unresolved[candidate] += 1
    return unresolved


def _call_llm(names: list[str]) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _PROMPT},
            {"role": "user", "content": json.dumps(names, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=8000,
    )
    return json.loads(response.choices[0].message.content)


def _merge_entry(kb: dict[str, Any], key: str, value: dict[str, Any], raw: str) -> None:
    entry = kb.setdefault(key, {})
    for field in (
        "deciduous",
        "fall_colors",
        "beautiful_flowers",
        "blooming_season",
        "explanation",
    ):
        if value.get(field) not in (None, ""):
            entry.setdefault(field, value[field])
    for field in ("common_names", "chinese_common_names"):
        existing = entry.setdefault(field, [])
        for item in value.get(field) or []:
            item = str(item).strip()
            if item and item not in existing:
                existing.append(item)
    if raw and raw.lower() != key:
        existing = entry.setdefault("common_names", [])
        if raw not in existing and len(raw) < 80:
            existing.append(raw)


def enrich(cities: list[CitySpec], *, dry_run: bool = False) -> dict[str, int]:
    resolver = SpeciesResolver()
    unresolved = _read_unresolved(cities, resolver)
    names = [name for name, _ in unresolved.most_common()]
    print(f"Unresolved unique names: {len(names):,} ({sum(unresolved.values()):,} rows)")
    if not names:
        return {"batches": 0, "names": 0}

    if dry_run:
        for name, count in unresolved.most_common(40):
            print(f"  {count:6d}  {name}")
        return {"batches": 0, "names": len(names)}

    kb = resolver.kb
    aliases: dict[str, str] = {}
    if DEFAULT_ALIASES.exists():
        with DEFAULT_ALIASES.open(encoding="utf-8") as handle:
            aliases = json.load(handle)

    batches = 0
    for start in range(0, len(names), BATCH_SIZE):
        batch = names[start : start + BATCH_SIZE]
        batches += 1
        print(f"  [llm] batch {batches}: {len(batch)} names")
        try:
            result = _call_llm(batch)
        except Exception as exc:  # keep going; the cache is still valid
            print(f"    [error] {exc}")
            continue

        # Build a case-insensitive lookup because models sometimes change case.
        by_lower = {str(k).strip().lower(): v for k, v in result.items() if isinstance(v, dict)}
        for raw in batch:
            value = by_lower.get(raw.strip().lower())
            if not value:
                print(f"    [miss] {raw}")
                continue
            scientific = str(value.get("scientific_name") or "").strip()
            key = norm_key(scientific) if scientific else norm_key(raw)
            if not key:
                print(f"    [skip] {raw}")
                continue
            _merge_entry(kb, key, value, raw)
            aliases[raw] = key

    if not dry_run:
        tmp_kb = DEFAULT_KB.with_suffix(".json.tmp")
        with tmp_kb.open("w", encoding="utf-8") as handle:
            json.dump(kb, handle, ensure_ascii=False, indent=1)
        tmp_kb.replace(DEFAULT_KB)

        tmp_aliases = DEFAULT_ALIASES.with_suffix(".json.tmp")
        with tmp_aliases.open("w", encoding="utf-8") as handle:
            json.dump(aliases, handle, ensure_ascii=False, indent=1, sort_keys=True)
        tmp_aliases.replace(DEFAULT_ALIASES)

    print(f"Knowledge base now has {len(kb):,} entries; wrote {len(aliases):,} aliases")
    return {"batches": batches, "names": len(names)}
