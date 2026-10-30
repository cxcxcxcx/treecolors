
import pandas as pd
import os.path
import json
from pyproj import Transformer
from tree_data import group_by_specifies, export_groups_as_json, build_geojson, find_center_and_zoom, build_map, get_shared_tree_map, project_root

# Define file paths for San Jose data

san_jose_raw_data_file = os.path.join(project_root, 'data', 'raw', 'Street_Tree_San_Jose.csv')
san_jose_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_san_jose.json')
san_jose_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_san_jose.geojson')

# --- Function Definitions (assuming these are defined elsewhere or in a preceding cell) ---
# def group_by_specifies(...): ...
# def export_groups_as_json(...): ...
# class TreeSpeciesMap: ...
# def find_center_and_zoom(...): ...
# def deterministic_color(...): ...
# def hsl_to_hex(...): ...
# def format_tree_info(...): ...
# def build_map(...): ...


# --- Data Loading and Transformation ---
if os.path.exists(san_jose_raw_data_file):
    print(f"Loading raw data from {san_jose_raw_data_file}")
    sj_pd = pd.read_csv(san_jose_raw_data_file)
    print("Raw data loaded.")

    # Apply transformation (assuming transformer is defined elsewhere or in the cell)
    # If transformer is not defined, you'll need to define it here or in a preceding cell
    transformer = Transformer.from_crs("EPSG:2227", "EPSG:4326") # Adjust CRS if needed for San Jose data
    sj_pd['LATITUDE'], sj_pd['LONGITUDE'] = transformer.transform(sj_pd['X'], sj_pd['Y'])
    print("Coordinates transformed.")
else:
    print(f"Raw data file not found at {san_jose_raw_data_file}. Please ensure the file exists.")
    sj_pd = pd.DataFrame() # Create an empty DataFrame if the file is not found


if not sj_pd.empty:
    # --- Data Grouping ---
    if os.path.exists(san_jose_summary_file):
        print(f"Loading grouped data from {san_jose_summary_file}")
        with open(san_jose_summary_file, 'r') as f:
            # Need to convert list of dict back to the desired tuple format
            loaded_data = json.load(f)
            groups = [(item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']]) for item in loaded_data]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        # Adjust column names if necessary for San Jose data (e.g., 'NAMESCIENTIFIC')
        groups = group_by_specifies(sj_pd, 'NAMESCIENTIFIC', 'LATITUDE', 'LONGITUDE', 1000)
        export_groups_as_json(groups, san_jose_summary_file)
        print(f"Grouped data saved to {san_jose_summary_file}")

    # --- Fetch Tree Information ---
    # species_list = [g[0] for g in groups[:80]]
    tree_map_all_big = get_shared_tree_map()
    
    # --- Build GeoJSON (San Jose) ---
    print("Building San Jose GeoJSON...")
    # Adjust column names if necessary for San Jose data (e.g., 'LATITUDE', 'LONGITUDE')
    center_lat_lng, zoom_level = find_center_and_zoom(sj_pd, 'LATITUDE', 'LONGITUDE')
    if center_lat_lng:
      geojson_data_sj = build_geojson(groups[:80], tree_map_all_big.species_data)
      with open(san_jose_geojson_file, 'w') as f:
          json.dump(geojson_data_sj, f, indent=2)
      print(f"San Jose GeoJSON saved to {san_jose_geojson_file}")
    else:
      print("Could not determine map center and zoom level from data.")

else:
    print("Cannot process empty DataFrame.")