import os.path
import json
import pandas as pd
from tree_data import (
    group_by_specifies,
    export_groups_as_json,
    build_geojson,
    find_center_and_zoom,
    build_map,
    get_shared_tree_map,
    project_root,
)

# Define file paths for San Francisco data
sf_raw_data_file = os.path.join(project_root, 'Street_Tree_List_20251103.csv')
sf_summary_file = os.path.join(project_root, 'tree_summary_sf.json')
sf_map_file = os.path.join(project_root, 'web/sf.html')
sf_geojson_file = os.path.join(project_root, 'trees_sf.geojson')

# --- Data Loading and Preparation ---
if os.path.exists(sf_raw_data_file):
    print(f"Loading raw data from {sf_raw_data_file}")
    sf_df = pd.read_csv(sf_raw_data_file)
    print("Raw data loaded.")

    # Ensure coordinate columns are numeric and drop rows missing required data
    sf_df['Latitude'] = pd.to_numeric(sf_df['Latitude'], errors='coerce')
    sf_df['Longitude'] = pd.to_numeric(sf_df['Longitude'], errors='coerce')
    sf_df['qSpecies'] = sf_df['qSpecies'].astype(str).str.strip()
    sf_df['Species'] = (
        sf_df['qSpecies']
        .str.split('::', n=1)
        .str[0]
        .str.strip()
    )
    initial_count = len(sf_df)
    sf_df = sf_df.dropna(subset=['Latitude', 'Longitude', 'Species'])
    sf_df = sf_df[sf_df['Species'].str.len() > 0]
    dropped_count = initial_count - len(sf_df)
    if dropped_count:
        print(f"Dropped {dropped_count} rows with missing coordinates or species.")
else:
    print(f"Raw data file not found at {sf_raw_data_file}. Please ensure the file exists.")
    sf_df = pd.DataFrame()

if not sf_df.empty:
    # --- Data Grouping ---
    if os.path.exists(sf_summary_file):
        print(f"Loading grouped data from {sf_summary_file}")
        with open(sf_summary_file, 'r') as f:
            loaded_data = json.load(f)
            groups = [
                (item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']])
                for item in loaded_data
            ]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        groups = group_by_specifies(sf_df, 'Species', 'Latitude', 'Longitude', 1000)
        export_groups_as_json(groups, sf_summary_file)
        print(f"Grouped data saved to {sf_summary_file}")

    # --- Fetch Tree Information ---
    tree_map_all_big = get_shared_tree_map()

    # --- Build GeoJSON ---
    print("Building San Francisco GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(sf_df, 'Latitude', 'Longitude')
    if center_lat_lng:
        geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
        with open(sf_geojson_file, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        print(f"San Francisco GeoJSON saved to {sf_geojson_file}")

        # --- Build Map (disabled by default) ---
        # Uncomment the following lines to also generate the folium map
        # print("Building San Francisco map...")
        # m = build_map(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
        # m.save(sf_map_file)
        # print(f"Map saved to {sf_map_file}")
    else:
        print("Could not determine map center and zoom level from data.")
else:
    print("Cannot process empty DataFrame.")
