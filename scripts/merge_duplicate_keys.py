#!/usr/bin/env python3
"""Merge knowledge-base entries that are keyed by a common name into the
binomial entry for the same tree.

Some city inventories record "Red maple" where another records "Acer rubrum".
Both became separate KB keys, so the map, the species panel and the plate
generator treat one tree as two species.

The binomial key always survives. The common-name entry contributes any
missing traits, its common names, and an alias, then is removed.

Usage:
    python3 scripts/merge_duplicate_keys.py --dry-run
    python3 scripts/merge_duplicate_keys.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = PROJECT_ROOT / "data" / "tree_info" / "species_info.json"
ALIAS_PATH = PROJECT_ROOT / "data" / "tree_info" / "species_aliases.json"
PLATE_DIRS = [PROJECT_ROOT / "samples" / "plates80", PROJECT_ROOT / "web" / "plates"]

TRAIT_FIELDS = ("deciduous", "fall_colors", "beautiful_flowers")


def slugify(key: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in key.lower()).strip("_")


ENGLISH_TOKENS = {
    "common", "red", "white", "green", "black", "blue", "golden", "silver",
    "dwarf", "japanese", "chinese", "european", "american", "sweet", "wild",
    "mountain", "river", "swamp", "scarlet", "yellow", "purple", "pink",
    "ornamental", "autumn", "flowering", "weeping", "southern", "northern",
    "eastern", "western", "hybrid", "pin", "sour", "bitter", "big", "little",
    "tall", "small", "upright", "columnar", "globe", "hardy", "dwarf",
}


def genus_tokens(kb: dict, aliases: dict) -> set[str]:
    """First tokens that behave like botanical genera.

    Derived from alias targets, which are binomials by construction: a token
    that heads at least three of them is a genus.  Common English words are
    excluded so that "red maple" is never mistaken for a binomial.
    """
    counts: Counter[str] = Counter()
    for value in aliases.values():
        tokens = str(value).split()
        if len(tokens) >= 2 and re.fullmatch(r"[a-z]{3,}", tokens[0]):
            counts[tokens[0]] += 1
    return {
        token for token, count in counts.items()
        if count >= 3 and token not in ENGLISH_TOKENS
    }


def find_pairs(kb: dict, genera: set[str]) -> list[tuple[str, str]]:
    def is_binomial(key: str) -> bool:
        tokens = key.split()
        return len(tokens) >= 2 and tokens[0] in genera

    by_common: dict[str, list[str]] = defaultdict(list)
    for key, entry in kb.items():
        for name in entry.get("common_names") or []:
            by_common[name.strip().lower()].append(key)

    pairs: dict[str, str] = {}
    for key in kb:
        if is_binomial(key):
            continue
        candidates = [k for k in by_common.get(key.lower(), []) if k != key and is_binomial(k)]
        if candidates:
            pairs[key] = pick_survivor(candidates)

    for key, entry in kb.items():
        if not is_binomial(key):
            continue
        for name in entry.get("common_names") or []:
            other = name.strip().lower()
            if other in kb and other != key and not is_binomial(other) and other not in pairs:
                pairs[other] = key

    return sorted(pairs.items())


def pick_survivor(candidates: list[str]) -> str:
    """Prefer a plain binomial over a cultivar or a genus-level placeholder."""
    def score(key: str) -> tuple[int, int, int]:
        tokens = key.split()
        placeholder = 1 if tokens[-1] in {"sp", "spp", "spp."} else 0
        cultivar = 1 if ("'" in key or tokens[-1].startswith("x")) else 0
        return (placeholder, cultivar, len(tokens))
    return sorted(candidates, key=score)[0]


def merge_entry(target: dict, source: dict, common_key: str) -> dict:
    merged = dict(target)
    for field in TRAIT_FIELDS:
        merged[field] = bool(target.get(field)) or bool(source.get(field))
    for field in ("blooming_season", "explanation"):
        if not str(merged.get(field) or "").strip() and str(source.get(field) or "").strip():
            merged[field] = source[field]
    names: list[str] = []
    for name in list(target.get("common_names") or []) + list(source.get("common_names") or []) + [common_key]:
        name = str(name).strip()
        if name and name.lower() not in {n.lower() for n in names}:
            names.append(name)
    merged["common_names"] = names
    chinese: list[str] = []
    for name in list(target.get("chinese_common_names") or []) + list(source.get("chinese_common_names") or []):
        name = str(name).strip()
        if name and name not in chinese:
            chinese.append(name)
    if chinese:
        merged["chinese_common_names"] = chinese
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry run)")
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    args = parser.parse_args()
    apply = args.apply and not args.dry_run

    kb = json.loads(KB_PATH.read_text())
    aliases = json.loads(ALIAS_PATH.read_text())
    pairs = find_pairs(kb, genus_tokens(kb, aliases))
    print(f"duplicate keys to merge: {len(pairs)}")

    for common_key, target_key in pairs[:15]:
        print(f"  {common_key!r} -> {target_key!r}")
    if len(pairs) > 15:
        print(f"  ... and {len(pairs) - 15} more")

    if not apply:
        print("dry run: nothing written")
        return 0

    stamp = ".bak-merge"
    for path in (KB_PATH, ALIAS_PATH):
        backup = path.with_suffix(path.suffix + stamp)
        if not backup.exists():
            shutil.copy2(path, backup)

    moved_plates = 0
    for common_key, target_key in pairs:
        merged = merge_entry(kb[target_key], kb[common_key], common_key)
        kb[target_key] = merged
        for name in (kb[common_key].get("common_names") or []) + [common_key]:
            name = str(name).strip().lower()
            if name and name not in aliases:
                aliases[name] = target_key
        del kb[common_key]
        if merged.get("common_names"):
            aliases[common_key] = target_key
        source_slug, target_slug = slugify(common_key), slugify(target_key)
        if source_slug != target_slug:
            for directory in PLATE_DIRS:
                source_plate = directory / f"{source_slug}.png"
                target_plate = directory / f"{target_slug}.png"
                if source_plate.exists() and not target_plate.exists():
                    source_plate.rename(target_plate)
                    moved_plates += 1

    KB_PATH.write_text(json.dumps(kb, indent=2, ensure_ascii=False) + "\n")
    ALIAS_PATH.write_text(json.dumps(aliases, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"merged {len(pairs)} keys, moved {moved_plates} plate files, "
          f"KB now {len(kb)} entries, aliases {len(aliases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
