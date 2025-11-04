import pandas as pd
import requests
import json
import os.path
from pyproj import Transformer
from tree_data import group_by_specifies, export_groups_as_json, build_geojson, find_center_and_zoom, build_map, get_shared_tree_map, project_root


palo_alto_raw_data_file = os.path.join(project_root, 'TreeData_PaloAlto_all.json')
palo_alto_summary_file = os.path.join(project_root, 'tree_summary_palo_alto.json')
palo_alto_map_file = os.path.join(project_root, 'palo_alto.html')
palo_alto_geojson_file = os.path.join(project_root, 'trees_palo_alto.geojson')


# --- Data Fetching and Transformation ---
if os.path.exists(palo_alto_raw_data_file):
    print(f"Loading raw data from {palo_alto_raw_data_file}")
    with open(palo_alto_raw_data_file, 'r') as f:
        all_full_data = json.load(f)
    # Reconstruct the 'features' list from the batched data
    all_data_features = []
    for batch in all_full_data:
        if 'features' in batch:
            all_data_features.extend(batch['features'])

    if all_data_features:
        df = pd.DataFrame([{**feature['attributes'], **feature['geometry']} for feature in all_data_features])
        print("Raw data loaded and converted to DataFrame.")
    else:
        print("No features found in raw data.")
        df = pd.DataFrame() # Create an empty DataFrame if no data is found

else:
    print("Fetching raw data from API...")
    def build_fetch_url(offset, count):
        return f'https://services6.arcgis.com/evmyRZRrsopdeog7/arcgis/rest/services/TreeData/FeatureServer/0/query?f=json&where=1%3D1&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=STREET%2CLATITUDE%2CLONGITUDE%2CSPECIES%2CTREEID%2CJURISDICTION%2CLOCATIONID%2CHEIGHTCODE%2CCANOPYWIDTH&orderByFields=OBJECTID%20ASC&outSR=102643&resultOffset={offset}&resultRecordCount={count}'

    all_data = []
    all_full_data = []
    total_elements = 39629
    batch_size = 1000
    for offset in range(0, total_elements, batch_size):
        count = min(batch_size, total_elements - offset)
        url = build_fetch_url(offset, count)
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()
                all_data.extend(data['features'])
                all_full_data.append(data)
                print(f"Fetched {len(data['features'])} elements from {offset}")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error decoding JSON response at offset {offset}: {e}")
                print(f"Response content: {response.text}") #print the response to help debug
        else:
            print(f"Error fetching data from {url}: Status code {response.status_code}")

    if all_data:
        df = pd.DataFrame([{**feature['attributes'], **feature['geometry']} for feature in all_data])
        print("Raw data fetched and converted to DataFrame.")
        # Save raw data
        with open(palo_alto_raw_data_file, 'w') as f:
            json.dump(all_full_data, f)
            print(f"Raw data saved to {palo_alto_raw_data_file}")
    else:
        print("No data fetched.")
        df = pd.DataFrame() # Create an empty DataFrame if no data is fetched

if not df.empty:
    # Apply transformation
    transformer = Transformer.from_crs("EPSG:2227", "EPSG:4326")
    df['LATITUDE'], df['LONGITUDE'] = transformer.transform(df['x'], df['y'])
    print("Coordinates transformed.")

    # --- Data Grouping ---
    if os.path.exists(palo_alto_summary_file):
        print(f"Loading grouped data from {palo_alto_summary_file}")
        with open(palo_alto_summary_file, 'r') as f:
            # Need to convert list of dict back to the desired tuple format
            loaded_data = json.load(f)
            groups = [(item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']]) for item in loaded_data]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        groups = group_by_specifies(df, 'SPECIES', 'LATITUDE', 'LONGITUDE', 1000)
        export_groups_as_json(groups, palo_alto_summary_file)
        print(f"Grouped data saved to {palo_alto_summary_file}")

    # --- Fetch Tree Information ---
    # Get species list for potential additional fetching
    species_list = [g[0] for g in groups[:80]]
    tree_map_all_big = get_shared_tree_map(additional_species=species_list)

    # --- Build GeoJSON ---
    print("Building GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(df, 'LATITUDE', 'LONGITUDE')
    if center_lat_lng:
      geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
      with open(palo_alto_geojson_file, 'w') as f:
          json.dump(geojson_data, f, indent=2)
      print(f"GeoJSON saved to {palo_alto_geojson_file}")
      
      # --- Build Map (disabled by default) ---
      # Uncomment the following lines to also generate the folium map
      # print("Building map...")
      # m = build_map(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
      # m.save(palo_alto_map_file)
      # print(f"Map saved to {palo_alto_map_file}")
    else:
      print("Could not determine map center and zoom level from data.")

else:
    print("Cannot process empty DataFrame.")
