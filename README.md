# Bay Area Tree Map Project

This project visualizes tree data for various cities, primarily in the Bay Area (and now expanding to other regions like Vancouver).

## Directory Structure

The project follows a specific directory structure to organize data and scripts:

- **`data/`**: The main data directory.
    - **`raw/`**: Contains raw input files (CSVs, ZIPs, JSONs) downloaded from city open data portals.
    - **`tree_info/`**: Contains JSON files with AI-generated tree species information (e.g., `tree_info_palo_alto_1000_gpt4o.json`).
    - **`output/`**: Contains generated output files.
        - **`geojson/`**: Generated GeoJSON files for each city (e.g., `trees_palo_alto.geojson`).
        - **`summary/`**: Intermediate summary JSON files (e.g., `tree_summary_palo_alto.json`).
        - `trees.mbtiles`: The final vector tileset generated from all GeoJSONs.
- **`py/`**: Contains Python scripts for data processing.
    - `pgcloud.py`: Main script for fetching data from pg-cloud.com based cities.
    - `tree_data.py`: Shared utilities for processing tree data, species mapping, and GeoJSON generation.
    - `run_*.py`: Individual scripts for processing specific cities (e.g., `run_vancouver.py`, `run_palo_alto.py`).
- **`web/`**: Contains the frontend web application.
- **`build_tiles.sh`**: Shell script to generate the `trees.mbtiles` file using `tippecanoe`.

## How to Add a New City

To add a new city to the map, follow these steps:

1.  **Obtain Data**: Find a source for the city's tree data (usually a CSV or Shapefile from an open data portal).

2.  **Create a Processing Script**:
    - Create a new Python script in `py/` named `run_<city_name>.py`.
    - Use existing scripts (e.g., `py/run_vancouver.py` or `py/run_berkeley.py`) as a template.
    - The script should:
        - Download the raw data to `data/raw/`.
        - Load and clean the data (standardize column names, handle missing coordinates).
        - **Species Name**: Construct a clean species name. Ideally use `Genus Species` format (e.g., "Acer rubrum"). Fallback to Common Name if Scientific Name is unavailable or poor quality.
        - Group data by species using `tree_data.group_by_specifies`.
        - Save a summary JSON to `data/output/summary/`.
        - Fetch/Update tree info using `tree_data.get_shared_tree_map`.
        - Generate a GeoJSON file to `data/output/geojson/`.

3.  **Update `build_tiles.sh`**:
    - Add the new GeoJSON file path to the `tippecanoe` command in `build_tiles.sh`.

4.  **Run the Pipeline**:
    - Run your python script: `python3 py/run_<city_name>.py`
    - Run the tile builder: `./build_tiles.sh`

## Running the Pipeline

1.  **Process Data**:
    Run the individual city scripts to update their GeoJSONs.
    ```bash
    python3 py/run_vancouver.py
    # ... run other scripts as needed
    ```

2.  **Build Tiles**:
    Generate the vector tileset.
    ```bash
    ./build_tiles.sh
    ```
    This will create `data/output/trees.mbtiles` and convert it to `web/trees.pmtiles`.

## Dependencies

- Python 3
- pandas, requests, geopandas, shapely, pyproj
- `tippecanoe` (for tile generation)
- `pmtiles` (for converting mbtiles to pmtiles)
