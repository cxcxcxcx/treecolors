import os
import requests
import pandas as pd
import json
from tree_data import (
    group_by_specifies,
    export_groups_as_json,
    build_geojson,
    find_center_and_zoom,
    get_shared_tree_map,
    project_root,
)

# Define file paths
vancouver_url = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/public-trees/exports/csv?lang=en&timezone=America%2FLos_Angeles&use_labels=true&delimiter=%3B"
vancouver_raw_data_file = os.path.join(project_root, 'data', 'raw', 'trees_vancouver.csv')
vancouver_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_vancouver.json')
vancouver_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_vancouver.geojson')

def download_data():
    if not os.path.exists(vancouver_raw_data_file):
        print(f"Downloading Vancouver data from {vancouver_url}...")
        response = requests.get(vancouver_url)
        response.raise_for_status()
        with open(vancouver_raw_data_file, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded to {vancouver_raw_data_file}")
    else:
        print(f"File already exists at {vancouver_raw_data_file}")

def process_data():
    if not os.path.exists(vancouver_raw_data_file):
        print("Raw data file not found.")
        return

    print(f"Loading raw data from {vancouver_raw_data_file}")
    # The URL says delimiter is ';', so we use sep=';'
    df = pd.read_csv(vancouver_raw_data_file, sep=';')
    print("Raw data loaded.")
    
    # Parse coordinates from geo_point_2d
    # Format: "49.20939799877542, -123.12279900016271"
    def parse_coordinates(geo_point):
        if pd.isna(geo_point):
            return None, None
        try:
            lat, lng = map(float, geo_point.split(','))
            return lat, lng
        except ValueError:
            return None, None

    coords = df['geo_point_2d'].apply(parse_coordinates)
    df['Latitude'] = [c[0] for c in coords]
    df['Longitude'] = [c[1] for c in coords]

    # Use GENUS_NAME + SPECIES_NAME, fallback to COMMON_NAME
    def get_species_name(row):
        genus = str(row['GENUS_NAME']).strip()
        species = str(row['SPECIES_NAME']).strip()
        common = str(row['COMMON_NAME']).strip()
        
        full_name = ""
        if genus and genus.lower() != 'nan' and species and species.lower() != 'nan':
            full_name = f"{genus} {species}"
        
        if not full_name or full_name.lower() == 'nan nan':
            if common and common.lower() != 'nan':
                return common.title()
            return ""
            
        return full_name.title()

    df['Species'] = df.apply(get_species_name, axis=1)
    
    # Drop rows with missing data
    initial_count = len(df)
    df = df.dropna(subset=['Latitude', 'Longitude', 'Species'])
    df = df[df['Species'].str.len() > 0]
    df = df[df['Species'] != 'Nan']
    dropped_count = initial_count - len(df)
    if dropped_count:
        print(f"Dropped {dropped_count} rows with missing coordinates or species.")

    if not df.empty:
        # --- Data Grouping ---
        if os.path.exists(vancouver_summary_file):
            print(f"Loading grouped data from {vancouver_summary_file}")
            with open(vancouver_summary_file, 'r') as f:
                loaded_data = json.load(f)
                groups = [
                    (item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']])
                    for item in loaded_data
                ]
            print("Grouped data loaded.")
        else:
            print("Grouping data by species...")
            groups = group_by_specifies(df, 'Species', 'Latitude', 'Longitude', 1000)
            export_groups_as_json(groups, vancouver_summary_file)
            print(f"Grouped data saved to {vancouver_summary_file}")

        # --- Fetch Tree Information ---
        # Get species list for potential additional fetching
        species_list = [g[0] for g in groups[:80]]
        tree_map_all_big = get_shared_tree_map(additional_species=species_list)

        # --- Build GeoJSON ---
        print("Building Vancouver GeoJSON...")
        center_lat_lng, zoom_level = find_center_and_zoom(df, 'Latitude', 'Longitude')
        if center_lat_lng:
            geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
            with open(vancouver_geojson_file, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            print(f"Vancouver GeoJSON saved to {vancouver_geojson_file}")
        else:
            print("Could not determine map center and zoom level from data.")
    else:
        print("Cannot process empty DataFrame.")

if __name__ == "__main__":
    download_data()
    process_data()
