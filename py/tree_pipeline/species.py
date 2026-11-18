"""Species-name resolution against the curated tree-knowledge base.

The knowledge base (``data/tree_info/tree_info_palo_alto_1000_gpt4o.json``)
contains a mix of scientific keys and legacy common-name keys.  This resolver
therefore builds:

* ``exact_full``: keys with cultivar words preserved (``ulmus frontier``);
* ``exact_base``: base species/genus keys only (``acer rubrum``, ``ulmus``);
* ``alias``: every ``common_names`` entry mapped back to its KB key.

It understands the messy forms found in real city inventories: cultivar quotes,
parentheticals, ``spp.``/``var.``/``ssp.`` suffixes, hybrid ``x``, comma-inverted
common names (``Oak, Willow``), and ``SCIENTIFIC - COMMON``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KB = PROJECT_ROOT / "data" / "tree_info" / "species_info.json"
DEFAULT_ALIASES = PROJECT_ROOT / "data" / "tree_info" / "species_aliases.json"

_INVALID_PREFIXES = (
    "vacant",
    "stump",
    "unknown",
    "other",
    "no tree",
    "not a tree",
    "planting site",
    "wooded area",
    "private tree",
    "empty pit",
    "scheduled planting",
    "tree requested",
    "unplantable",
    "under process",
    "not city",
    "wca worked",
    "homeowner refused",
    "rescon",
    "_work",
    "n/a",
    "n a",
    "not applicable",
    "none",
    # Pasadena's inventory carries internal planting codes with no species.
    "zadd",
    # Ventura and La Mesa use these for empty planting sites; Anaheim uses its
    # own wording for the same thing.
    "unsuitable",
    "no replant",
    "not city planted",
    # Ventura rows whose geometry outlived the species record, and tree wells
    # that were paved over (Santa Monica).
    "tree site",
    "asphalted",
)
_INVALID_EXACT = {
    "",
    "stump",
    "other",
    "other species",
    "other (see notes)",
    "no tree",
    "wooded area",
    "unknown tree",
    "unknown dead",
    "unknown shrub",
    "private tree",
    "n a",
    # La Mesa uses the leaf habit as the species value for one row.
    "deciduous",
}

_QUOTE_RE = re.compile(r"[\"'‘’“”`][^\"'‘’“”`]*[\"'‘’“”`]")
_PAREN_RE = re.compile(r"\([^)]*\)")
_BRACKET_RE = re.compile(r"\[[^\]]*\]")
_SPACE_RE = re.compile(r"\s+")
_CULTIVAR_RE = re.compile(r"[\"'‘’“”]")
_GENUS_LEVEL_RE = re.compile(r"\b(spp?\.?|species)\s*$", re.I)
_SUBSPECIES_RE = re.compile(r"\b(ssp|subsp|var|v)\.?\s+", re.I)


def clean_name(raw: str) -> str:
    """Return a lookup-friendly form with cultivar/parenthetical noise removed."""

    value = str(raw).replace("\xa0", " ").replace("×", "x").strip()
    value = value.replace("–", "-").replace("—", "-")
    value = _PAREN_RE.sub(" ", value)
    value = re.sub(r"\([^)]*$", " ", value)
    value = _BRACKET_RE.sub(" ", value)
    value = _QUOTE_RE.sub(" ", value)
    if " - " in value:
        value = value.split(" - ", 1)[0]
    # Strip taxonomic suffixes only at word boundaries.  A naive
    # ``replace(" sp", "")`` corrupts "Quercus species" -> "Quercusecies".
    value = re.sub(r"\s+spp?\.?\s*$", "", value, flags=re.I)
    value = re.sub(r"\s+species\s*$", "", value, flags=re.I)
    value = re.sub(r"\s+(?:ssp|subsp|var|v)\.?\s+", " ", value, flags=re.I)
    value = _SPACE_RE.sub(" ", value).strip(" .,;:-")
    return value


def norm_full(value: str) -> str:
    """Normalize without removing cultivar words (used for exact key matching)."""

    value = str(value).replace("\xa0", " ").replace("×", "x").lower()
    value = re.sub(r"[^a-z0-9 ]", " ", value)
    return _SPACE_RE.sub(" ", value).strip()


def norm_key(value: str) -> str:
    """Base-key normalization: cultivar noise removed, punctuation ignored."""

    return norm_full(clean_name(value))


def _base_key_allowed(key: str) -> bool:
    """Whether a KB key may act as a base species/genus key.

    Cultivar keys must not populate the base index.  For example,
    ``ulmus 'frontier'`` must not become the base entry for ``Ulmus``.
    """

    if _CULTIVAR_RE.search(key):
        return False
    tokens = key.split()
    if len(tokens) <= 2:
        return True
    # Platanus x acerifolia is a real hybrid species, not a cultivar.
    return len(tokens) == 3 and tokens[1].lower() == "x"


def _candidates(raw: str) -> list[tuple[str, str]]:
    """Return ``(kind, value)`` candidates; kind is ``full`` or ``base``."""

    cleaned = clean_name(raw)
    raw_tokens = cleaned.split()
    genus_level = bool(_GENUS_LEVEL_RE.search(raw)) or len(raw_tokens) == 1

    candidates: list[tuple[str, str]] = [("full", raw), ("base", cleaned)]

    if ";" in cleaned:
        candidates.extend(("base", part.strip()) for part in cleaned.split(";") if part.strip())

    if "," in cleaned:
        first, second = cleaned.split(",", 1)
        first, second = first.strip(), second.strip()
        if first and second:
            candidates.append(("base", f"{second} {first}"))

    if re.search(r"\bx\b", cleaned, flags=re.I):
        candidates.append(("base", re.sub(r"\bx\b\s*", "", cleaned, flags=re.I).strip()))

    tokens = cleaned.split()
    if len(tokens) > 2:
        candidates.append(("base", " ".join(tokens[:2])))
        if tokens[1].lower() == "x" and len(tokens) > 3:
            candidates.append(("base", f"{tokens[0]} {tokens[2]}"))
        if _SUBSPECIES_RE.search(raw):
            # Acer tataricum ssp. ginnala -> Acer ginnala
            candidates.append(("base", f"{tokens[0]} {tokens[-1]}"))

    if genus_level and tokens:
        candidates.append(("base", tokens[0]))

    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for kind, value in candidates:
        marker = (kind, norm_full(value) if kind == "full" else norm_key(value))
        if marker[1] and marker not in seen:
            seen.add(marker)
            unique.append((kind, value))
    return unique


def _smart_title(value: str) -> str:
    """Binomial in sentence case, cultivar left as published but title-cased.

    Pasadena publishes ``FRAXINUS VELUTINA 'modesto'``: all caps except the
    cultivar, so the whole string is neither upper nor lower and a plain
    ``isupper()`` test misses it.  Split the cultivar off before deciding.
    """

    value = _SPACE_RE.sub(" ", value).strip()
    if not value:
        return value

    split = _CULTIVAR_RE.search(value)
    head = (value[: split.start()] if split else value).strip()
    cultivar = value[split.start():] if split else ""

    tokens = head.split()
    if head.isupper() or head.islower():
        if len(tokens) >= 2 and all(token.isalpha() for token in tokens[:2]):
            head = tokens[0].capitalize() + " " + " ".join(t.lower() for t in tokens[1:])
        else:
            head = head.title()

    if cultivar:
        cultivar = _QUOTE_RE.sub(
            lambda m: f"'{m[0][1:-1].strip().title()}'" if m[0].strip("'") else m[0],
            cultivar,
        )
    return f"{head} {cultivar}".strip()


def is_invalid(raw: str) -> bool:
    key = norm_key(raw)
    if not key or key in _INVALID_EXACT:
        return True
    return any(key.startswith(prefix) for prefix in _INVALID_PREFIXES)


@dataclass(frozen=True)
class Resolution:
    key: str
    info: dict[str, Any]
    display: str
    match: str


class SpeciesResolver:
    def __init__(self, kb_path: Path = DEFAULT_KB, alias_path: Path = DEFAULT_ALIASES):
        self.kb_path = kb_path
        with kb_path.open(encoding="utf-8") as handle:
            self.kb: dict[str, dict[str, Any]] = json.load(handle)
        self.extra_aliases: dict[str, str] = {}
        if alias_path.exists():
            with alias_path.open(encoding="utf-8") as handle:
                self.extra_aliases = json.load(handle)

        self.exact_full: dict[str, str] = {}
        self.exact_base: dict[str, str] = {}
        self.alias: dict[str, str] = {}
        for key, info in self.kb.items():
            self.exact_full.setdefault(norm_full(key), key)
            if _base_key_allowed(key):
                self.exact_base.setdefault(norm_key(key), key)
            for part in key.split(";"):
                if _base_key_allowed(part):
                    self.exact_base.setdefault(norm_key(part), key)
            for common in info.get("common_names") or []:
                alias_key = norm_key(common)
                if alias_key:
                    self.alias.setdefault(alias_key, key)
        for alias, key in self.extra_aliases.items():
            if key in self.kb:
                self.alias.setdefault(norm_key(alias), key)
        self._cache: dict[str, Resolution | None] = {}

    def _lookup(self, kind: str, value: str) -> tuple[str, str] | None:
        if kind == "full":
            key = norm_full(value)
            if key in self.exact_full:
                return self.exact_full[key], "exact"
            return None
        key = norm_key(value)
        if key in self.exact_base:
            return self.exact_base[key], "exact"
        if key in self.alias:
            return self.alias[key], "alias"
        return None

    def resolve(self, raw: str) -> Resolution | None:
        if raw in self._cache:
            return self._cache[raw]

        if is_invalid(raw):
            self._cache[raw] = None
            return None

        for kind, candidate in _candidates(raw):
            hit = self._lookup(kind, candidate)
            if hit is None:
                continue
            kb_key, match = hit
            self._cache[raw] = Resolution(
                kb_key, self.kb[kb_key], _smart_title(candidate), match
            )
            return self._cache[raw]

        self._cache[raw] = None
        return None

    def unresolved_species(self, names: list[str]) -> list[str]:
        return [name for name in names if self.resolve(name) is None]


def load_resolver(kb_path: Path = DEFAULT_KB) -> SpeciesResolver:
    if not kb_path.exists():
        raise SystemExit(f"Species knowledge base not found: {kb_path}")
    return SpeciesResolver(kb_path)
