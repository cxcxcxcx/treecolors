"""Add KB entries and aliases for the inventories added in November 2026.

Napa, La Mesa, Ventura, Santa Monica and Signal Hill, then Atherton.  The run
is idempotent: entries and aliases that already exist are skipped, so it can be
re-run after appending a new city's names.

    PYTHONPATH=py python3 scripts/apply_new_city_species.py

To rebuild from scratch, ``git checkout`` the two data files first:

    PYTHONPATH=py python3 scripts/apply_new_city_species.py

Why this is a script and not a hand edit: the botanically correct name and the
name the inventory already resolves to are sometimes the same tree (Camphora
officinarum / Cinnamomum camphora, Melaleuca citrina / Callistemon citrinus,
Searsia lancea / Rhus lancea), and sometimes not (the KB's "fern pine" entries
point at Podocarpus, but the Santa Monica inventory gives Afrocarpus gracilior
where Ventura gives Afrocarpus falcatus).  Each case is written down here so a
later reader can see which was decided and on what basis.

Adding a new KB key for a name that already resolves is what created duplicate
species earlier (a common-name key and its binomial), so the rule is: add an
entry only when the KB has no key for the species at all, and otherwise add an
alias that points at the key the trees already use.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "data" / "tree_info" / "species_info.json"
ALIAS_PATH = ROOT / "data" / "tree_info" / "species_aliases.json"


def entry(
    deciduous: bool,
    fall_colors: bool,
    beautiful_flowers: bool,
    blooming_season: str,
    chinese: list[str],
    common: list[str],
    explanation: str,
) -> dict:
    return {
        "deciduous": deciduous,
        "fall_colors": fall_colors,
        "beautiful_flowers": beautiful_flowers,
        "blooming_season": blooming_season,
        "chinese_common_names": chinese,
        "common_names": common,
        "explanation": explanation,
    }


# Canonical name -> traits.  Evergreen unless noted.
#
# Renamed-the-same-tree aliases (no new entry):
#   Camphora officinarum      -> cinnamomum camphora
#   Melaleuca citrina         -> callistemon citrinus
#   Melaleuca viminalis       -> callistemon viminalis
#   Corymbia maculata         -> "spotted gum" (the old common-name key; the
#                                separate eucalyptus maculata entry is the
#                                red-spotted gum, a different tree)
#   Searsia lancea            -> rhus lancea
#   Butia odorata             -> butia capitata
#   Syzygium austale          -> syzygium australe (existing key)
#   Xylosma congesta          -> xylosma congestum (existing key)
#   Salix lasiolepsis         -> salix lasiolepis (new entry: no salix key had
#                                it, and "arroyo willow" was a common-name key)
NEW_ENTRIES = {
    "archontophoenix cunninghamiana": entry(
        False, False, False, "Summer", ["假槟榔", "国王椰子"],
        ["Bangalow Palm", "Piccabeen Palm"],
        "A tall Australian feather palm with arching fronds, widely planted "
        "in California; the 'Bangalow' of Ventura's inventory.  The KB already "
        "carries 'king palm' as a common-name key with the same traits.",
    ),
    "afrocarpus macrophyllus": entry(
        False, False, False, "N/A", ["大叶非洲罗汉松"],
        ["Shrubby Yew Pine"],
        "A podocarp formerly placed in Podocarpus, grown in California as a "
        "sheared hedge and as the dark-leaved cultivar 'Maki'.  Santa Monica "
        "and Ventura differ on Afrocarpus falcatus vs gracilior as 'fern pine', "
        "so this species gets its own entry rather than an alias.",
    ),
    "bauhinia forficata": entry(
        True, False, True, "Spring", ["巴西羊蹄甲", "白花羊蹄甲"],
        ["Brazilian Orchid Tree"],
        "A Brazilian tree with white orchid-like flowers, deciduous but "
        "without autumn colour.",
    ),
    "salix lasiolepis": entry(
        True, False, False, "Spring", ["阿罗约柳"],
        ["Arroyo Willow"],
        "A fast-growing western North American willow along streams; "
        "deciduous but without autumn colour.",
    ),
    "eucalyptus amplifolia": entry(
        False, False, False, "N/A", ["大叶桉", "卷心菜桉"],
        ["Cabbage Gum"],
        "A New South Wales gum with broad, glossy leaves, planted in "
        "California as an ornamental shade tree; evergreen.",
    ),
    "eucalyptus conferruminata": entry(
        False, False, False, "N/A", ["蜘蛛桉"],
        ["Spider Gum", "Bald Island Marlock"],
        "A small Western Australian eucalypt with fused buds and spider-like "
        "flowers, used in California as a hedge and screen plant.",
    ),
    "erythrina bidwillii": entry(
        True, False, True, "Summer", ["比氏刺桐"],
        ["Bidwill's Coral Tree"],
        "A hybrid coral tree with red flowers over a long season; deciduous "
        "but with no autumn display.",
    ),
    "catalpa hybrida": entry(
        True, False, True, "Late Spring to Early Summer", ["杂交梓树"],
        ["Hybrid Catalpa"],
        "A hybrid catalpa, usually Catalpa bignonioides x ovata, grown for "
        "its large leaves and orchid-like flowers.",
    ),
    "eugenia aggregata": entry(
        False, False, True, "Spring", ["聚合番樱桃", "樱桃番樱桃"],
        ["Cherry of the Rio Grande", "Rio Grande Cherry"],
        "A small evergreen South American tree with edible dark red fruit, "
        "planted in mild California gardens.",
    ),
    "pinus elliottii": entry(
        False, False, False, "Spring", ["湿地松", "沼泽松"],
        ["Slash Pine", "Swamp Pine"],
        "A fast-growing southeastern US pine, evergreen, occasionally "
        "planted in California as a specimen.",
    ),
    "nyssa aquatica": entry(
        True, True, False, "Spring", ["水紫树", "水生蓝果树"],
        ["Water Tupelo"],
        "A southeastern US swamp tree with red autumn colour; in California it "
        "grows only where the roots reach water.",
    ),
    "camellia sasanqua": entry(
        False, False, True, "Fall to Winter", ["茶梅"],
        ["Sasanqua Camellia", "Sasanqua"],
        "An evergreen East Asian camellia that flowers from autumn into "
        "winter, commonly grown as a hedge in California.",
    ),
    "sambucus nigra": entry(
        True, False, True, "Early Summer", ["西洋接骨木", "黑接骨木"],
        ["European Black Elderberry", "Black Elder"],
        "The European elderberry, deciduous, with flat heads of creamy "
        "flowers and black fruit; no autumn display.",
    ),
    "sambucus mexicana": entry(
        True, False, True, "Spring", ["墨西哥接骨木"],
        ["Mexican Elderberry"],
        "A western North American elderberry, often treated as a subspecies "
        "of Sambucus nigra; deciduous, no autumn colour.  The KB already has "
        "'blue elderberry' as a common-name key (Sambucus caerulea).",
    ),
    "quercus edulis": entry(
        False, False, False, "Spring", ["食用石栎", "日本石栎"],
        ["Japanese False Oak", "Shii Oak"],
        "The evergreen 'shii' of Japan, formerly Lithocarpus edulis and "
        "Pasania edulis, grown as an ornamental in California.",
    ),
    "pittosporum floribundum": entry(
        False, False, False, "N/A", ["喜马拉雅海桐"],
        ["Himalayan Pittosporum"],
        "An evergreen Himalayan pittosporum, planted in California for its "
        "dense foliage; sometimes sold as P. viridiflorum.",
    ),
    "brachychiton bidwillii": entry(
        False, False, True, "Spring to Summer", ["小火焰树", "比氏瓶木"],
        ["Little Kurrajong"],
        "A small Queensland bottle tree that flowers on bare stems; evergreen "
        "in mild climates.",
    ),
    "hakea suaveolens": entry(
        False, False, True, "Spring", ["甜哈克木"],
        ["Sweet Hakea"],
        "A Western Australian hakea with scented white flowers, evergreen, "
        "planted in California as a screening shrub.",
    ),
    "citrus aurantifolia": entry(
        False, False, True, "Spring", ["来檬", "酸橙"],
        ["Key Lime", "Mexican Lime"],
        "The key lime, an evergreen citrus; the KB also carries the spelling "
        "Citrus x aurantiifolia.",
    ),
    "frangula californica": entry(
        False, False, False, "Spring", ["加州鼠李"],
        ["Coffeeberry"],
        "A California native evergreen shrub, formerly Rhamnus californica, "
        "used in native plantings; small greenish flowers.",
    ),
    "auranticarpa rhombifolia": entry(
        False, False, False, "N/A", ["金叶海桐"],
        ["Diamond-leaved Pittosporum"],
        "An evergreen Queensland tree with diamond-shaped leaves, formerly "
        "Pittosporum rhombifolium; grown in California as a screen.",
    ),
    "howea belmoreana": entry(
        False, False, False, "N/A", ["贝尔莫棕"],
        ["Sentry Palm", "Belmore Sentry Palm"],
        "A Lord Howe Island feather palm with a more upright, stiffer crown "
        "than the Kentia palm; evergreen.",
    ),
    "cycas thouarsii": entry(
        False, False, False, "N/A", ["马达加斯加苏铁"],
        ["Madagascar Cycad", "Queen Sago"],
        "A large cycad from Madagascar and East Africa, evergreen, planted in "
        "mild California gardens.",
    ),
    # Atherton (records-request workbook, added after the five above).
    "torreya californica": entry(
        False, False, False, "N/A", ["加州榧", "加州榧树"],
        ["California Nutmeg", "California Torreya"],
        "A native California conifer related to yews, with stiff, sharp, "
        "glossy needles and olive-like seeds; evergreen.",
    ),
}

# Inventory spelling -> canonical key.  Botanical names that already resolve
# are included where a spelling variant would otherwise reappear as a second
# key.  No alias may point at a key that a different common-name key already
# owns; scripts/check_species_keys.py guards that.
NEW_ALIASES = {
    "Archontophoenix cunninghamiana": "archontophoenix cunninghamiana",
    "Archontophoenix maxima": "king palm",
    "Afrocarpus macrophyllus": "afrocarpus macrophyllus",
    "Afrocarpus macrophyllus 'Maki'": "afrocarpus macrophyllus",
    "Cassia leptophylla": "gold medallion tree",
    "Phoenix roebelenii": "pygmy date palm",
    "Jubaea chilensis": "chilean wine palm",
    "Ravenea rivularis": "majesty palm",
    "Dypsis decaryi": "triangle palm",
    "Quercus tomentella": "island oak",
    "Pyrus betulifolia": "pyrus calleryana",
    "Ceiba speciosa": "silk-floss tree",
    "Harpephyllum caffrum": "kaffir plum",
    "Araucaria heterophylla": "star pine",
    "Araucaria bidwillii": "bunya-bunya",
    "Araucaria columnaris": "cook pine",
    "Handroanthus heptaphyllus": "pink trumpet tree",
    "Handroanthus avellanedae": "pink trumpet tree",
    "Bauhinia forficata": "bauhinia forficata",
    "Brahea brandegeei": "san jose hesper palm",
    "Corymbia maculata": "spotted gum",
    "Salix lasiolepsis": "salix lasiolepis",
    "Salix lasiolepis": "salix lasiolepis",
    "Eucalyptus amplifolia": "eucalyptus amplifolia",
    "Eucalyptus conferruminata": "eucalyptus conferruminata",
    "Eucalyptus cornuta": "yate",
    "Erythrina bidwillii": "erythrina bidwillii",
    "Catalpa hybrida": "catalpa hybrida",
    "Eugenia aggregata": "eugenia aggregata",
    "Pinus elliottii": "pinus elliottii",
    "Nyssa aquatica": "nyssa aquatica",
    "Camellia sasanqua": "camellia sasanqua",
    "Sambucus nigra": "sambucus nigra",
    "Sambucus mexicana": "sambucus mexicana",
    "Sambucus neomexicana": "sambucus mexicana",
    "Quercus edulis": "quercus edulis",
    "Pasania edulis": "quercus edulis",
    "Pittosporum floribundum": "pittosporum floribundum",
    "Brachychiton bidwillii": "brachychiton bidwillii",
    "Brachychiton bidwilli": "brachychiton bidwillii",
    "Hakea suaveolens": "hakea suaveolens",
    "Citrus aurantifolia": "citrus aurantifolia",
    "Frangula californica": "frangula californica",
    "Rhamnus californica": "frangula californica",
    "Auranticarpa rhombifolia": "auranticarpa rhombifolia",
    "Auranticarpa rhombifolium": "auranticarpa rhombifolia",
    "Howea belmoreana": "howea belmoreana",
    "Cycas thouarsii": "cycas thouarsii",
    "Torreya californica": "torreya californica",
    # ── synonyms: the same tree under its former name ────────────────────
    "Camphora officinarum": "cinnamomum camphora",
    "Melaleuca citrina": "callistemon citrinus",
    "Melaleuca viminalis": "callistemon viminalis",
    "Melaleuca rigidus": "callistemon citrinus",
    "Callistemon rigidus": "callistemon citrinus",
    "Searsia lancea": "rhus lancea",
    "Butia odorata": "butia capitata",
    "Syzygium austale": "syzygium australe",
    "Xylosma congesta": "xylosma congestum",
    "Pyrus betulifolia 'Dancer'": "pyrus calleryana",
    "Dancer Pear": "pyrus calleryana",
    "Prunus amygdalus": "prunus dulcis",
    "Cupressus nootkatensis": "callitropsis nootkatensis",
    "Hesperocyparis arizonica": "cupressus arizonica",
    "Salix lasiandra": "salix lucida",
    "Melaleuca genistifolia": "melaleuca (species)",
    "Leptospermum scopulorum": "leptospermum scoparium",
    # ── inventory spellings that were falling through to a second key ────
    "Parkinsonia X 'Desert Museum'": "desert museum palo verde",
    "x Hesperotropsis leylandii": "leyland cypress",
    "x Rhaphiobotrya splendens": "majestic beauty indian hawthorn",
    "x Rhaphiobotrya splendens 'Montic'": "majestic beauty indian hawthorn",
    "Ilex altaclarensis 'Wilsonii'": "ilex wilsonii",
    "Magnolia grandiflora-little gem": "little gem dwarf southern magnolia",
}


def main() -> None:
    with KB_PATH.open(encoding="utf-8") as handle:
        kb = json.load(handle)
    with ALIAS_PATH.open(encoding="utf-8") as handle:
        aliases = json.load(handle)

    before_kb = dict(kb)
    added = 0
    for key, value in NEW_ENTRIES.items():
        if key in kb:
            continue
        kb[key] = value
        added += 1

    new_aliases = 0
    for alias, key in NEW_ALIASES.items():
        if key not in kb:
            raise SystemExit(f"alias target missing from KB: {alias!r} -> {key!r}")
        if alias not in aliases:
            aliases[alias] = key
            new_aliases += 1

    _check_new_duplicates(before_kb, kb)

    with KB_PATH.open("w", encoding="utf-8") as handle:
        json.dump(kb, handle, ensure_ascii=False, indent=1)
    with ALIAS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(aliases, handle, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"KB entries added: {added} (now {len(kb):,})")
    print(f"aliases added: {new_aliases} (now {len(aliases):,})")


def _owner_pairs(kb: dict) -> set[tuple[str, str]]:
    """(common name, key) for a name shared by a binomial and a plain key."""
    owners: dict[str, set[str]] = {}
    for key, value in kb.items():
        for name in value.get("common_names") or []:
            owners.setdefault(str(name).strip().lower(), set()).add(key)
    pairs: set[tuple[str, str]] = set()
    for name, keys in owners.items():
        binomials = {k for k in keys if len(k.split()) > 1}
        commons = {k for k in keys if len(k.split()) <= 1}
        for binomial in binomials:
            for common in commons:
                pairs.add((name, binomial))
                pairs.add((name, common))
    return pairs


def _check_new_duplicates(before: dict, after: dict) -> None:
    """Fail if this run made a common name ambiguous in a new way.

    The KB already contains many such pairs (a genus key beside its species,
    e.g. 'oak' for Quercus and 'quercus species').  The panel only lists a
    species twice when both keys are *used*; those older pairs resolve to one
    key by the species index.  A pair created here is new and almost always a
    mistake, so it is an error rather than a warning.
    """
    new_pairs = _owner_pairs(after) - _owner_pairs(before)
    if not new_pairs:
        return
    by_name: dict[str, set[str]] = {}
    for name, key in new_pairs:
        by_name.setdefault(name, set()).add(key)
    lines = [f"{name!r}: {sorted(keys)}" for name, keys in sorted(by_name.items())]
    raise SystemExit(
        "this change gives one common name to two kinds of key:\n  " + "\n  ".join(lines)
    )


if __name__ == "__main__":
    main()
