import requests
import json
import os
import time
import random
import string
from datetime import datetime
import sys

# Add current directory to sys.path to ensure we can import tree_data
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tree_data import get_shared_tree_map, build_geojson

import math

# Configuration
BASE_URL = "https://pg-cloud.com/main/server/db.php"
LAYER_NAME = "trees"
OUTPUT_DIR = "data"

def generate_request_id():
    """Generates a random hex string for uniqueRequestID."""
    return ''.join(random.choices(string.hexdigits.lower(), k=16))

def get_all_tree_ids(folder_name, extent_coordinates, show_archived="0", max_features="100000"):
    """
    Step 1: Get the list of all Tree IDs (Primary IDs) within the city extent.
    Accepts folder_name (string), extent_coordinates (list of strings),
    show_archived (string, default '0'), and max_features (string, default '100000').
    """
    print(f"Fetching all tree IDs for folder '{folder_name}'...")

    # Dynamically construct HEADERS based on folder_name
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://pg-cloud.com/{folder_name}/",
        "Origin": "https://pg-cloud.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "action": "callFunction",
        "params[funcToCall]": "retrieveMapPointsStart",
        "params[args][folder]": folder_name, # Use passed folder_name
        "params[args][layerName]": LAYER_NAME,
        "params[args][uniqueRequestID]": generate_request_id(),
        "params[args][showArchived]": show_archived, # Use passed show_archived
        "params[args][geom_field]": "geom",
        "params[args][maxFeatures]": max_features, # Use passed max_features
        "params[args][filtersPkg][settings][andor]": "AND",

        # Extent coordinates (minX, minY, maxX, maxY)
        "params[args][extent][]": extent_coordinates # Use passed extent_coordinates
    }

    try:
        response = requests.post(BASE_URL, headers=HEADERS, data=payload)
        response.raise_for_status()

        data = response.json()

        if 'results' in data and 'pids' in data['results']:
            ids = data['results']['pids']
            total_count = data['results'].get('total', {}).get('count', 'Unknown')
            print(f"Found {len(ids)} trees (Server total: {total_count}).")
            return ids
        else:
            print("No data found in 'results.pids'. Response dump:", json.dumps(data)[:200])
            return []

    except Exception as e:
        print(f"Error fetching IDs: {e}")
        return []

def get_tree_details_chunk(pids_chunk, folder_name):
    """
    Step 2: Get details for a specific list of IDs.
    Accepts pids_chunk (list of int/str IDs) and folder_name (string).
    """
    pids_str = ",".join(map(str, pids_chunk))

    # Dynamically construct HEADERS for this function based on folder_name
    current_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://pg-cloud.com/{folder_name}/", # Use passed folder_name
        "Origin": "https://pg-cloud.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "action": "callFunction",
        "params[funcToCall]": "retrieveLayers",
        "params[args][folder]": folder_name, # Use passed folder_name
        "params[args][table]": LAYER_NAME,
        "params[args][uniqueRequestID]": generate_request_id(),
        "params[args][pids]": pids_str
    }

    try:
        response = requests.post(BASE_URL, headers=current_headers, data=payload)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and 'trees' in data['results'] and 'geojson' in data['results']['trees'] and 'features' in data['results']['trees']['geojson']:
            return data['results']['trees']['geojson']['features']
        return []

    except Exception as e:
        print(f"Error fetching chunk: {e}")
        return []

def web_mercator_to_latlon(x, y):
    """Converts Web Mercator (EPSG:3857) coordinates to Lat/Lon (EPSG:4326)."""
    lon = (x / 20037508.34) * 180.0
    lat = (y / 20037508.34) * 180.0
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon

def save_tree_summary(all_tree_data, folder_name):
    """
    Groups tree data by species and saves it in the requested summary format.
    """
    summary_data = {}

    for tree in all_tree_data:
        props = tree.get('properties', {})
        geometry = tree.get('geometry', {})
        
        # Get species name
        species_name = props.get('species_common_name')
        if not species_name:
             species_name = 'Unknown Species'
        
        # Get coordinates
        coordinates = geometry.get('coordinates', [])
        if len(coordinates) == 2:
            x, y = coordinates
            lat, lng = web_mercator_to_latlon(x, y)
            
            if species_name not in summary_data:
                summary_data[species_name] = []
            
            summary_data[species_name].append({
                "lat": lat,
                "lng": lng
            })

    # Convert to list format
    output_list = []
    for species, locations in summary_data.items():
        output_list.append({
            "species": species,
            "locations": locations
        })

    # Save to file
    filename = os.path.join(OUTPUT_DIR, f"tree_summary_{folder_name.lower()}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_list, f, indent=4)
    
    print(f"Tree summary saved to: {filename}")
    return output_list


def get_species_mapping(folder_name):
    """
    Step 1.5: Fetch species info to map species IDs to common names.
    Returns a dictionary {species_id: species_common_name}.
    """
    print(f"Fetching species info for folder '{folder_name}'...")
    
    HEADERS = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-client-version": "v3.9.3",
        "x-requested-with": "XMLHttpRequest",
        # Cookie is required to authenticate the request
        "cookie": "PHPSESSID=llf977tiukrjghiu799d1i6p9c; _ga=GA1.1.1170743925.1764087010; _ga_NEXVLPG3X9=GS2.1.s1764087009$o1$g1$t1764087165$j59$l0$h0",
        "Referer": f"https://pg-cloud.com/{folder_name}/",
        "Origin": "https://pg-cloud.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    # Payload reconstructed from user sample (action at the end)
    payload = {
        "params[fieldName]": "species_common",
        "params[filtersPkg][settings][andor]": "AND",
        "params[filtersPkg][settings][boundToResults]": "",
        "params[folder]": folder_name,
        "params[getPids]": "",
        "params[layerName]": LAYER_NAME,
        "params[colorGrad]": "Random",
        "params[characterSortType]": "abc",
        "params[numberBreaks]": "5",
        "params[to_fixed]": "1",
        "params[placeholders]": "",
        "params[type]": "",
        "params[reverse_order]": "",
        "params[dont_color_code]": "",
        "params[field2]": "",
        "params[break_out_multiple]": "",
        "params[is_multi_layer]": "",
        "params[format]": "",
        "params[changeToField]": "",
        "params[presetColors]": "",
        "params[count]": "",
        "params[limit]": "",
        "action": "getGroupsByCount"
    }

    response = requests.post(BASE_URL, headers=HEADERS, data=payload)
    response.raise_for_status()
    data = response.json()

    # Debug: Save raw species response
    debug_filename = os.path.join(OUTPUT_DIR, f"{folder_name}_species_debug.json")
    with open(debug_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw species response to {debug_filename}")

    mapping = {}
    if 'tt2' in data and isinstance(data['tt2'], list):
        for item in data['tt2']:
            val = item.get('val')
            alias = item.get('alias')
            if val is not None:
                mapping[val] = alias
        print(f"Fetched {len(mapping)} species mappings.")
    else:
        raise Exception("Warning: 'tt2' not found or invalid in species response.")
    
    return mapping

def scrape_city_trees(folder_name, extent_coordinates, show_archived="0", max_features="100000"):
    """
    Orchestrates the scraping of tree data for a given city folder and extent.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Get all IDs
    all_ids = get_all_tree_ids(folder_name, extent_coordinates, show_archived, max_features)

    # 1.5 Get Species Mapping
    species_map = get_species_mapping(folder_name)

    if not all_ids:
        print(f"No trees found for {folder_name}. Exiting scraping for this city.")
        return []

    # 2. Batch process to get details
    BATCH_SIZE = 2000 # Safe chunk size for URL encoded bodies
    all_tree_data = []

    total_chunks = (len(all_ids) + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"Downloading details for {folder_name} in {total_chunks} batches...")

    for i in range(0, len(all_ids), BATCH_SIZE):
        chunk = all_ids[i:i + BATCH_SIZE]
        current_batch = (i // BATCH_SIZE) + 1

        print(f"Processing batch {current_batch}/{total_chunks} for {folder_name}...")

        details = get_tree_details_chunk(chunk, folder_name)
        
        # Join species info
        for feature in details:
            props = feature.get('properties', {})
            sp_id = props.get('species_common')
            if sp_id in species_map:
                props['species_common_name'] = species_map[sp_id]
            else:
                 props['species_common_name'] = 'Unknown Species'

        all_tree_data.extend(details)

        # Be polite to the server
        time.sleep(0.5)

    # 3. Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"{folder_name.lower()}_trees_full_{timestamp}.json")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_tree_data, f, indent=2)

    print(f"\nSuccess! {len(all_tree_data)} tree records saved to: {filename}")
    
    # 4. Save summary format
    summary_data = save_tree_summary(all_tree_data, folder_name)

    # 5. Generate GeoJSON
    print("Building GeoJSON...")
    
    # Prepare data for build_geojson: list of (species, [(lat, lng), ...])
    groups = []
    for item in summary_data:
        species = item['species']
        locations = [(loc['lat'], loc['lng']) for loc in item['locations']]
        groups.append((species, locations))
    
    # Get tree info map
    species_list = [g[0] for g in groups]
    tree_map = get_shared_tree_map(additional_species=species_list)
    
    # Build GeoJSON
    geojson_data = build_geojson(groups, tree_map.species_data)
    
    geojson_filename = os.path.join(OUTPUT_DIR, f"trees_{folder_name.lower()}.geojson")
    with open(geojson_filename, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)
        
    print(f"GeoJSON saved to: {geojson_filename}")

    return all_tree_data

def main():
    # Define parameters for SanLeandroCA
    san_leandro_folder = "SanLeandroCA"
    san_leandro_extent = [
        "-13614382.411135172",
        "4523530.47036788",
        "-13597260.516799292",
        "4552500.104087961"
    ]

    # Call the new reusable scrape_city_trees function for SanLeandroCA
    print("\n--- Starting scraping for SanLeandroCA ---")
    scrape_city_trees(san_leandro_folder, san_leandro_extent)
    print("--- Finished scraping for SanLeandroCA ---\n")

    # Define parameters for FremontCA from the user's fetch call
    fremont_folder = "FremontCA"
    fremont_extent = [
        "-13593557.169324214",
        "4484157.9342681365",
        "-13559313.380652456",
        "4542097.201708301"
    ]

    # Call the new reusable scrape_city_trees function for FremontCA
    # Use show_archived="1" and max_features="2000" as per the user's provided fetch call
    print("\n--- Starting scraping for FremontCA ---")
    scrape_city_trees(fremont_folder, fremont_extent, show_archived="1")
    print("--- Finished scraping for FremontCA ---\n")

if __name__ == "__main__":
    main()