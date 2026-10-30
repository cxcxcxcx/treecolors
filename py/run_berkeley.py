import os.path
import json
import pandas as pd
import requests
import zipfile
import geopandas as gpd
from tree_data import (
    group_by_specifies,
    export_groups_as_json,
    build_geojson,
    find_center_and_zoom,
    build_map,
    get_shared_tree_map,
    project_root,
)

# Define file paths for Berkeley data
berkeley_download_url = 'https://spatial.lib.berkeley.edu/public/berkeley-s7gq2s/data.zip'
berkeley_zip_file = os.path.join(project_root, 'data', 'raw', 'berkeley_trees.zip')
berkeley_extract_dir = os.path.join(project_root, 'data', 'raw', 'berkeley_trees')
berkeley_raw_data_file = os.path.join(project_root, 'data', 'raw', 'City_Trees_Berkeley.csv')
berkeley_summary_file = os.path.join(project_root, 'data', 'output', 'summary', 'tree_summary_berkeley.json')
berkeley_geojson_file = os.path.join(project_root, 'data', 'output', 'geojson', 'trees_berkeley.geojson')

# --- Data Download and Loading ---
if os.path.exists(berkeley_raw_data_file):
    print(f"Loading raw data from {berkeley_raw_data_file}")
    berkeley_df = pd.read_csv(berkeley_raw_data_file)
    print("Raw data loaded.")
else:
    print(f"Raw data file not found. Downloading from {berkeley_download_url}...")
    
    # Download the shapefile
    if not os.path.exists(berkeley_zip_file):
        print("Downloading shapefile...")
        response = requests.get(berkeley_download_url)
        if response.status_code == 200:
            with open(berkeley_zip_file, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded shapefile to {berkeley_zip_file}")
        else:
            print(f"Error downloading file: Status code {response.status_code}")
            berkeley_df = pd.DataFrame()
    
    # Extract the shapefile
    if os.path.exists(berkeley_zip_file) and not os.path.exists(berkeley_extract_dir):
        print("Extracting shapefile...")
        with zipfile.ZipFile(berkeley_zip_file, 'r') as zip_ref:
            zip_ref.extractall(berkeley_extract_dir)
        print(f"Extracted shapefile to {berkeley_extract_dir}")
    
    # Find the shapefile in the extracted directory
    shapefile_path = None
    if os.path.exists(berkeley_extract_dir):
        for root, dirs, files in os.walk(berkeley_extract_dir):
            for file in files:
                if file.endswith('.shp'):
                    shapefile_path = os.path.join(root, file)
                    break
            if shapefile_path:
                break
    
    if shapefile_path and os.path.exists(shapefile_path):
        print(f"Reading shapefile from {shapefile_path}...")
        gdf = gpd.read_file(shapefile_path)
        print(f"Shapefile loaded. Found {len(gdf)} records.")
        
        # Extract coordinates from geometry
        if gdf.crs is not None and gdf.crs.to_string() != 'EPSG:4326':
            print(f"Converting CRS from {gdf.crs} to EPSG:4326...")
            gdf = gdf.to_crs('EPSG:4326')
        
        # Extract lat/lng from geometry
        gdf['Longitude'] = gdf.geometry.x
        gdf['Latitude'] = gdf.geometry.y
        
        # Find the species column (common names: SPECIES, SCIENTIFIC, COMMON_NAME, etc.)
        species_column = None
        possible_species_columns = ['SPECIES', 'SCIENTIFIC', 'COMMON_NAME', 'COMMON', 'NAME', 
                                   'TREE_NAME', 'SCIENTIFIC_NAME', 'GENUS_SPECIES', 'GENUSSPECIES']
        
        for col in possible_species_columns:
            if col in gdf.columns:
                species_column = col
                break
        
        if species_column is None:
            # Try to find any column that might contain species info
            print("Available columns:", gdf.columns.tolist())
            # Use the first text-like column as fallback, or ask user
            for col in gdf.columns:
                if col not in ['geometry', 'Latitude', 'Longitude'] and gdf[col].dtype == 'object':
                    species_column = col
                    print(f"Using '{col}' as species column. Please verify this is correct.")
                    break
        
        if species_column:
            berkeley_df = pd.DataFrame({
                'Latitude': gdf['Latitude'],
                'Longitude': gdf['Longitude'],
                'Species': gdf[species_column].astype(str).str.strip()
            })
            
            # Drop rows with missing data
            initial_count = len(berkeley_df)
            berkeley_df = berkeley_df.dropna(subset=['Latitude', 'Longitude', 'Species'])
            berkeley_df = berkeley_df[berkeley_df['Species'].str.len() > 0]
            berkeley_df = berkeley_df[berkeley_df['Species'] != 'nan']
            dropped_count = initial_count - len(berkeley_df)
            if dropped_count:
                print(f"Dropped {dropped_count} rows with missing coordinates or species.")
            
            # Save as CSV for future use
            berkeley_df.to_csv(berkeley_raw_data_file, index=False)
            print(f"Raw data saved to {berkeley_raw_data_file}")
        else:
            print("Could not find species column in shapefile.")
            berkeley_df = pd.DataFrame()
    else:
        print(f"Could not find shapefile in {berkeley_extract_dir}")
        berkeley_df = pd.DataFrame()

if not berkeley_df.empty:
    # --- Data Grouping ---
    if os.path.exists(berkeley_summary_file):
        print(f"Loading grouped data from {berkeley_summary_file}")
        with open(berkeley_summary_file, 'r') as f:
            loaded_data = json.load(f)
            groups = [
                (item['species'], [(loc['lat'], loc['lng']) for loc in item['locations']])
                for item in loaded_data
            ]
        print("Grouped data loaded.")
    else:
        print("Grouping data by species...")
        groups = group_by_specifies(berkeley_df, 'Species', 'Latitude', 'Longitude', 1000)
        export_groups_as_json(groups, berkeley_summary_file)
        print(f"Grouped data saved to {berkeley_summary_file}")

    # --- Fetch Tree Information ---
    # Get species list for potential additional fetching
    species_list = [g[0] for g in groups[:80]]
    tree_map_all_big = get_shared_tree_map(additional_species=species_list)

    # --- Build GeoJSON ---
    print("Building Berkeley GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(berkeley_df, 'Latitude', 'Longitude')
    if center_lat_lng:
        geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data)
        with open(berkeley_geojson_file, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        print(f"Berkeley GeoJSON saved to {berkeley_geojson_file}")
    else:
        print("Could not determine map center and zoom level from data.")
else:
    print("Cannot process empty DataFrame.")

