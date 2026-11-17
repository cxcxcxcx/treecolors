"""Unit tests for the species resolver.

Run from the repository root:

    PYTHONPATH=py python3 -m pytest -q py/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tree_pipeline.species import (  # noqa: E402
    _smart_title,
    clean_name,
    is_invalid,
    load_resolver,
)


def test_cultivar_is_reduced_to_species():
    resolver = load_resolver()
    hit = resolver.resolve("Platanus x acerifolia 'Bloodgood'")
    assert hit is not None
    assert hit.key == "platanus x acerifolia"


def test_cultivar_with_quotes_does_not_break_lookup():
    resolver = load_resolver()
    hit = resolver.resolve("Acer rubrum 'October Glory'")
    assert hit is not None
    assert hit.key.startswith("acer rubrum")


def test_comma_inverted_common_name():
    # The KB keys species by binomial (the merge of common-name keys), so "Oak, Willow"
    # must resolve through its inverted common name to the same species key.
    resolver = load_resolver()
    hit = resolver.resolve("Oak, Willow")
    assert hit is not None
    assert hit.key == "quercus phellos"
    assert hit.key == resolver.resolve("Willow Oak").key


def test_gender_parenthetical():
    resolver = load_resolver()
    hit = resolver.resolve("Ginkgo biloba (male)")
    assert hit is not None
    assert hit.key == "ginkgo biloba"


def test_genus_level_is_not_hijacked_by_cultivar():
    resolver = load_resolver()
    hit = resolver.resolve("Ulmus species")
    assert hit is not None
    assert hit.key == "ulmus spp."


def test_hybrid_prefix():
    resolver = load_resolver()
    hit = resolver.resolve("X Cupressocyparis leylandii")
    assert hit is not None
    assert hit.key == "cupressocyparis leylandii"


def test_placeholder_names_are_invalid():
    for value in ("Stump", "Vacant Site", "N/A", "Planting Site- Shade Tree", "unknown tree"):
        assert is_invalid(value), value


def test_species_clean_does_not_corrupt_species_word():
    assert clean_name("Quercus species") == "Quercus"
    assert clean_name("Acer spp.") == "Acer"


def test_common_eastern_species_are_present():
    resolver = load_resolver()
    for name in ("Taxodium distichum", "Fagus grandifolia", "Quercus bicolor", "Pinus strobus"):
        assert resolver.resolve(name) is not None, name


def test_bay_area_common_names_resolve():
    # Santa Clara's Lucity inventory names most trees by common name only, and the
    # aliases these depend on are easy to lose when the alias file is regenerated.
    resolver = load_resolver()
    expected = {
        "Flowering Pear": "pyrus calleryana",
        "Liquid Amber": "liquidambar styraciflua",
        "Fruitless Mulberry": "morus alba",
        "Camphor": "cinnamomum camphora",
        "Geijera": "geijera parviflora",
        "Redwood": "sequoia sempervirens",
        "Chinese Fringe": "chionanthus retusus",
        "Fruitless Olive": "olea europaea",
    }
    for name, key in expected.items():
        hit = resolver.resolve(name)
        assert hit is not None, name
        assert hit.key == key, f"{name} -> {hit.key}, expected {key}"


def test_bay_area_aliases_do_not_resolve_to_wrong_habit():
    # Camphor, Geijera and the redwood are evergreens; the others are deciduous.
    resolver = load_resolver()
    for name, deciduous in (
        ("Camphor", False),
        ("Geijera", False),
        ("Redwood", False),
        ("Flowering Pear", True),
        ("Liquid Amber", True),
    ):
        hit = resolver.resolve(name)
        assert hit is not None, name
        assert bool(hit.info.get("deciduous")) is deciduous, name


def test_smart_title_handles_uppercase_names_and_lowercase_cultivars():
    # Cupertino and Los Angeles ship all-caps names; Pasadena ships all caps
    # except a lower-cased cultivar.  Both must render like the rest of the map.
    assert _smart_title("ACACIA MELANOXYLON") == "Acacia melanoxylon"
    assert _smart_title("FRAXINUS VELUTINA 'modesto'") == "Fraxinus velutina 'Modesto'"
    assert _smart_title("PYRUS CALLERYANA 'BRADFORD'") == "Pyrus calleryana 'Bradford'"
    # Already-correct names are left exactly as published.
    assert _smart_title("Platanus x acerifolia 'Bloodgood'") == "Platanus x acerifolia 'Bloodgood'"
    assert _smart_title("Ginkgo biloba") == "Ginkgo biloba"
