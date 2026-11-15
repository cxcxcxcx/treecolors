"""Unit tests for the species resolver.

Run from the repository root:

    PYTHONPATH=py python3 -m pytest -q py/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tree_pipeline.species import clean_name, is_invalid, load_resolver  # noqa: E402


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
