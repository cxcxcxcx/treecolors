"""City-by-city tree data pipeline for the fall-colors map.

The legacy ``py/run_*.py`` scripts are kept for backwards compatibility. New
cities should be added to :mod:`tree_pipeline.cities` and run through the CLI::

    python -m tree_pipeline fetch --city washington_dc
    python -m tree_pipeline process --city washington_dc
    python -m tree_pipeline tiles
"""

__all__ = ["cities", "sources", "species", "export"]
