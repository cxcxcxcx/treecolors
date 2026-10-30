import pandas as pd
import os.path
import re
from pyproj import Transformer
from tree_data import group_by_specifies, build_geojson, find_center_and_zoom, get_shared_tree_map, project_root

# Define file paths
los_angeles_raw_data_file = os.path.join(project_root, 'data', 'raw', 'Trees__Bureau_of_Street_Services_.csv')
los_angeles_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_los_angeles.json')
los_angeles_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_los_angeles.geojson')

# --- Data Loading and Transformation ---
if os.path.exists(los_angeles_raw_data_file):
    print(f"Loading raw data from {los_angeles_raw_data_file}")
    df = pd.read_csv(los_angeles_raw_data_file)
    
    # Extract Botanical Name from TOOLTIP
    def extract_botanical_name(tooltip):
        if not isinstance(tooltip, str):
            return None
        match = re.search(r'Botanical Name: (.*?)(?:\\n|$)', tooltip)
        if match:
            name = match.group(1).strip()
            return name if name != "Not Specified" else None
        return None

    df['Botanical Name'] = df['TOOLTIP'].apply(extract_botanical_name)
    
    # Filter out missing botanical names
    df = df.dropna(subset=['Botanical Name'])
    
    if not df.empty:
        print("Raw data loaded and filtered.")
        
        # Transform coordinates
        # Input: EPSG:2229 (NAD83 / California Zone 5 (ftUS))
        # Output: EPSG:4326 (WGS 84)
        transformer = Transformer.from_crs("EPSG:2229", "EPSG:4326")
        df['LATITUDE'], df['LONGITUDE'] = transformer.transform(df['X'].values, df['Y'].values)
        print("Coordinates transformed.")

        # --- Data Grouping ---
        print("Grouping data by species...")
        # Using 'Botanical Name' as the species column
        groups = group_by_specifies(df, 'Botanical Name', 'LATITUDE', 'LONGITUDE', 1000)
        
        # --- Fetch Tree Information ---
        # Get species list for potential additional fetching
        species_list = [g[0] for g in groups[:80]]
        tree_map_all_big = get_shared_tree_map(additional_species=species_list)

        # --- Build GeoJSON ---
        print("Building GeoJSON...")
        center_lat_lng, zoom_level = find_center_and_zoom(df, 'LATITUDE', 'LONGITUDE')
        
        if center_lat_lng:
            geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
            with open(los_angeles_geojson_file, 'w') as f:
                import json
                json.dump(geojson_data, f, indent=2)
            print(f"GeoJSON saved to {los_angeles_geojson_file}")
        else:
            print("Could not determine map center and zoom level from data.")

    else:
        print("No valid data found after filtering.")

else:
    print(f"Raw data file not found: {los_angeles_raw_data_file}")
