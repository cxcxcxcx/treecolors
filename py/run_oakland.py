import os.path
import json
import pandas as pd
import re
from tree_data import (
    group_by_specifies,
    export_groups_as_json,
    build_geojson,
    find_center_and_zoom,
    build_map,
    get_shared_tree_map,
    project_root,
)

# Define file paths for Oakland data
data_dir = os.path.join(project_root, 'data', 'raw')
oakland_raw_data_file = os.path.join(data_dir, 'Oakland_Street_Trees_20251123.csv')
oakland_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_oakland.json')
oakland_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_oakland.geojson')

# --- Data Loading and Preparation ---
if os.path.exists(oakland_raw_data_file):
    print(f"Loading raw data from {oakland_raw_data_file}")
    oakland_df = pd.read_csv(oakland_raw_data_file)
    print("Raw data loaded.")
    
    # Parse coordinates from "Location 1" column
    # Format: "470 Oakland Ca  (37.80505999961946, -122.27301999967312)"
    def parse_coordinates(location_str):
        if pd.isna(location_str):
            return None, None
        # Extract coordinates from parentheses: (lat, lng)
        match = re.search(r'\(([-\d.]+),\s*([-\d.]+)\)', str(location_str))
        if match:
            lat = float(match.group(1))
            lng = float(match.group(2))
            return lat, lng
        return None, None
    
    # Extract coordinates
    coords = oakland_df['Location 1'].apply(parse_coordinates)
    oakland_df['Latitude'] = [c[0] for c in coords]
    oakland_df['Longitude'] = [c[1] for c in coords]
    
    # Clean species column
    oakland_df['Species'] = oakland_df['SPECIES'].astype(str).str.strip()
    
    # Drop rows with missing data
    initial_count = len(oakland_df)
    oakland_df = oakland_df.dropna(subset=['Latitude', 'Longitude', 'Species'])
    oakland_df = oakland_df[oakland_df['Species'].str.len() > 0]
    oakland_df = oakland_df[oakland_df['Species'] != 'nan']
    oakland_df = oakland_df[oakland_df['Species'] != 'Unknown']
    dropped_count = initial_count - len(oakland_df)
    if dropped_count:
        print(f"Dropped {dropped_count} rows with missing coordinates or species.")
else:
    print(f"Raw data file not found at {oakland_raw_data_file}. Please ensure the file exists.")
    oakland_df = pd.DataFrame()

if not oakland_df.empty:
    # --- Data Grouping ---
    if os.path.exists(oakland_summary_file):
        print(f"Loading grouped data from {oakland_summary_file}")
        with open(oakland_summary_file, 'r') as f:
            loaded_data = json.load(f)
            groups = [
                (item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']])
                for item in loaded_data
            ]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        groups = group_by_specifies(oakland_df, 'Species', 'Latitude', 'Longitude', 1000)
        export_groups_as_json(groups, oakland_summary_file)
        print(f"Grouped data saved to {oakland_summary_file}")

    # --- Fetch Tree Information ---
    # Get species list for potential additional fetching
    species_list = [g[0] for g in groups[:80]]
    tree_map_all_big = get_shared_tree_map(additional_species=species_list)

    # --- Build GeoJSON ---
    print("Building Oakland GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(oakland_df, 'Latitude', 'Longitude')
    if center_lat_lng:
        geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
        with open(oakland_geojson_file, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        print(f"Oakland GeoJSON saved to {oakland_geojson_file}")
    else:
        print("Could not determine map center and zoom level from data.")
else:
    print("Cannot process empty DataFrame.")

