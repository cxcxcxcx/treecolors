import pandas as pd
import os.path
import json
from tree_data import group_by_specifies, export_groups_as_json, build_geojson, find_center_and_zoom, build_map, get_shared_tree_map, project_root

# Define file paths for Cupertino data
cupertino_raw_data_file = os.path.join(project_root, 'data', 'raw', 'Trees_cupertino.csv')
cupertino_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_cupertino.json')
cupertino_map_file = os.path.join(project_root, 'data', 'output', 'cupertino.html')
cupertino_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_cupertino.geojson')

# --- Data Loading and Transformation ---
if os.path.exists(cupertino_raw_data_file):
    print(f"Loading raw data from {cupertino_raw_data_file}")
    # Specify dtype for columns causing mixed type warning if needed
    cupertino_pd = pd.read_csv(cupertino_raw_data_file, dtype={'PlanningProject1': str, 'PlanningProject2': str})
    print("Raw data loaded.")

    # Handle coordinate issues (swap LAT and LONG if LAT < 0)
    # Assuming 'LAT' and 'LONG' columns exist in the Cupertino data
    cupertino_pd.loc[cupertino_pd['LAT'] < 0, ['LAT', 'LONG']] = cupertino_pd.loc[cupertino_pd['LAT'] < 0, ['LONG', 'LAT']].values
    print("Coordinates checked and swapped if necessary.")

else:
    print(f"Raw data file not found at {cupertino_raw_data_file}. Please ensure the file exists.")
    cupertino_pd = pd.DataFrame() # Create an empty DataFrame if the file is not found


if not cupertino_pd.empty:
    # --- Data Grouping ---
    if os.path.exists(cupertino_summary_file):
        print(f"Loading grouped data from {cupertino_summary_file}")
        with open(cupertino_summary_file, 'r') as f:
            # Need to convert list of dict back to the desired tuple format
            loaded_data = json.load(f)
            groups = [(item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']]) for item in loaded_data]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        # Adjust column names if necessary for Cupertino data (e.g., 'Species', 'LAT', 'LONG')
        groups = group_by_specifies(cupertino_pd, 'Species', 'LAT', 'LONG', 1000)
        export_groups_as_json(groups, cupertino_summary_file)
        print(f"Grouped data saved to {cupertino_summary_file}")

    # --- Fetch Tree Information ---
    tree_map_all_big = get_shared_tree_map()
    
    # --- Build GeoJSON ---
    print("Building Cupertino GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(cupertino_pd, 'LAT', 'LONG')
    if center_lat_lng:
      geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
      with open(cupertino_geojson_file, 'w') as f:
          json.dump(geojson_data, f, indent=2)
      print(f"Cupertino GeoJSON saved to {cupertino_geojson_file}")
      
      # --- Build Map (disabled by default) ---
      # Uncomment the following lines to also generate the folium map
      # print("Building map...")
      # m = build_map(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
      # m.save(cupertino_map_file)
      # print(f"Map saved to {cupertino_map_file}")
    else:
      print("Could not determine map center and zoom level from data.")

else:
    print("Cannot process empty DataFrame.")