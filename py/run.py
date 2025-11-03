import pandas as pd
import requests
import json
import os.path
import pyproj
from pyproj import Transformer
import hashlib
import random
import colorsys

# Define file paths
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

palo_alto_raw_data_file = os.path.join(project_root, 'TreeData_PaloAlto_all.json')
palo_alto_summary_file = os.path.join(project_root, 'tree_summary_palo_alto.json')
palo_alto_info_file = os.path.join(project_root, 'tree_info_palo_alto_1000_gpt4o.json')
palo_alto_map_file = os.path.join(project_root, 'palo_alto.html')
palo_alto_geojson_file = os.path.join(project_root, 'trees_palo_alto.geojson')

# --- Function Definitions ---
def group_by_specifies(df, species_column: str, lat_column: str, lng_column: str, top_n: int):
    grouped = df.groupby(species_column)
    top_species = grouped.size().sort_values(ascending=False).head(top_n).index

    result_list = []
    for species in top_species:
        species_data = grouped.get_group(species)
        rows = species_data.to_dict(orient='records')  # Convert rows to a list of dictionaries
        latlngs = list(zip(species_data[lat_column], species_data[lng_column]))
        result_list.append((species, latlngs))
    return result_list

def export_groups_as_json(groups, filename):
    """Exports groups data as JSON, keeping 6 decimal places for locations.

    Args:
        groups: A list of tuples, where each tuple contains:
            - species name (str)
            - a list of (latitude, longitude) tuples.
        filename: The name of the output JSON file.
    """

    data = []
    for species, locations in groups:
        formatted_locations = [
            {"lat": round(lat, 6), "lng": round(lng, 6)} for lat, lng in locations
        ]
        data.append({
            'species': species,
            'locations': formatted_locations
        })

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

class TreeSpeciesMap:
    MAX_FETCH_BATCH = 30  # Example batch size

    def __init__(self):
        self.species_data = {}

    def add_species_by_list(self, species_list):
        new_species = [s.lower() for s in species_list if s.lower() not in self.species_data and s.lower().replace(' ', '_') not in self.species_data]
        for i in range(0, len(new_species), self.MAX_FETCH_BATCH):
            batch = new_species[i:i + self.MAX_FETCH_BATCH]
            batch_data = self._fetch_tree_info_batch(batch)
            self.species_data.update(batch_data)

    def _fetch_tree_info_batch(self, species_batch):
      print('fetching', species_batch)
      from openai import OpenAI
      # NOTE: Make sure you have set the OPENAI_API_KEY environment variable
      # or replace 'sk-proj-...' with your actual API key
      # os.environ['OPENAI_API_KEY'] = 'sk-proj-REVOKED'
      client = OpenAI()
      response = client.chat.completions.create(
        # model="gpt-4o-mini",
        model="gpt-4o",
        messages=[
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": "Produce a JSON, for each of the tree below as key (lower case), show a list of common names, if the tree is decidious, if it's known for fall colors, if it's known for beautiful flowers, season of blooming, Chinese common names and an explanation."
                """
                Example: {'scientific name': {
                  'deciduous': true,
                  'fall_colors', true,
                  'beautiful_flowers': false,
                  'blooming_season': 'N/A',
                  'chinese_common_names': [],
                  'common_names': ['common_name']
                  'explanation': '....'
                  }, ...}"""
                + "\n".join(species_batch)
              }
            ]
          }
        ],
        response_format={
          "type": "json_object"
        },
        temperature=1,
        max_tokens=10000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
      )
      tree_obj = json.loads(response.choices[0].message.content)
      # print(tree_obj)
      # tree_info_map = {t['scientific_name'].lower(): t for t in tree_obj['trees']}
      return {k.lower(): v for k, v in tree_obj.items()}


    def save_as_json_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.species_data, f, indent=4)

def find_center_and_zoom(df, lat_column='LAT', lng_column='LONG'):
    """
    Finds the center and map zoom level for a given DataFrame.

    Args:
        df: The input DataFrame with latitude and longitude columns.
        lat_column: The name of the latitude column.
        lng_column: The name of the longitude column.

    Returns:
        A tuple containing the center coordinates (latitude, longitude) and the zoom level.
        Returns (None, None) if no valid coordinates are found.
    """

    # Filter out rows with latitude or longitude equal to 0
    valid_coordinates = df[(df[lat_column] != 0) & (df[lng_column] != 0)]

    if valid_coordinates.empty:
        return None, None

    center_lat = valid_coordinates[lat_column].mean()
    center_lng = valid_coordinates[lng_column].mean()

    # Calculate the zoom level based on the lat/lng range (adjust as needed)
    # A more sophisticated method might involve calculating the bounding box and zoom level
    lat_range = valid_coordinates[lat_column].max() - valid_coordinates[lat_column].min()
    lng_range = valid_coordinates[lng_column].max() - valid_coordinates[lng_column].min()

    zoom_level = 12  # Default zoom level
    if lat_range > 0.1 or lng_range > 0.1:
        zoom_level = 10  # Adjust based on your data spread
    elif lat_range < 0.001 and lng_range < 0.001:
      zoom_level = 15

    return (center_lat, center_lng), zoom_level

def deterministic_color(species, color_range='green'):
    """
    Generates a deterministic HSL color based on the species name and color range.

    Args:
        species: The name of the tree species (string).
        color_range: The desired color range ('green', 'red', or 'orange').

    Returns:
        A hex color code (string).
    """

    # Use SHA-256 to create a deterministic hash of the species name
    hash_object = hashlib.sha256(species.encode())
    hex_dig = hash_object.hexdigest()
    seed = int(hex_dig, 16)

    # Use the hash as a seed for the random number generator
    random.seed(seed)

    # Define HSL ranges based on color_range
    if color_range == 'green':
        h_range = (0.2, 0.4)  # Greenish hues
        s_range = (0.7, 1)
        l_range = (0.2, 0.4)  # Light to bright lightness
    elif color_range == 'red':
        h_range = (0.8, 1) # Pink to red hues
        s_range = (0.5, 1.0) # High saturation
        l_range = (0.3, 0.6) # Moderate lightness
    elif color_range == 'orange':
      return 'orange'
        # h_range = (0.05, 0.1)  # Orange hues
        # s_range = (0.6, 0.9) # High saturation
        # l_range = (0.4, 0.7)  # Moderate lightness
    elif color_range == 'brown':
        h_range = (0, 0.1) # Pink to red hues
        s_range = (0.2, 0.6)
        l_range = (0.05, 0.15) # Moderate lightness
    else:
        raise ValueError("Invalid color_range. Choose 'green', 'red', or 'orange'.")

    # Generate random HSL values within the specified ranges
    h = random.uniform(*h_range)
    s = random.uniform(*s_range)
    l = random.uniform(*l_range)

    # Convert HSL to hex and return
    return hsl_to_hex(h, s, l)

def hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))

def format_tree_info(species, tree_data):
    """Formats tree information as HTML for a popup."""

    # if species.lower() not in tree_info_map:
    #     return "<p>No information found for this species.</p>"

    # tree_data = tree_info_map[species.lower()]
    # <p><b>Deciduous:</b> {tree_data.get('deciduous', 'N/A')}</p>
    # <p><b>Fall Colors:</b> {tree_data.get('fall_colors', 'N/A')}</p>
    # <p><b>Beautiful Flowers:</b> {tree_data.get('beautiful_flowers', 'N/A')}</p>
    # <p><b>Blooming Season:</b> {tree_data.get('blooming_season', 'N/A')}</p>
    # <p><b>Chinese Common Names:</b> {', '.join(tree_data.get('chinese_common_names', ['N/A']))}</p>
    html = f"""
    <div><b>Species:</b> {species}</div>
    <div><b>Common Names:</b> {', '.join(tree_data.get('common_names', ['N/A']))}</div>
    <div><b>Explanation:</b> {tree_data.get('explanation', 'N/A')}</div>
    """
    return html


def build_map(top_trees, tree_info_map, center_lat_lng, zoom_level):
    import folium
    m = folium.Map(location=center_lat_lng, zoom_start=zoom_level, width=800, height=500)
    for species, xys in top_trees:
        lower_species = species.lower()
        if 'Vacant' in species or 'OBSOLETE' in species or species == 'Stump' or 'unknown' in lower_species:
            print('skipping', species)
            continue
        tree_info = tree_info_map.get(species.lower())
        if tree_info is None:
            tree_info = tree_info_map.get(species.lower().replace(' ', '_'))
        if tree_info is None:
            print(f"No information found for {species}")
            continue
        is_deciduous = tree_info['deciduous']
        # print(species, tree_info)
        group_1 = folium.FeatureGroup(species).add_to(m)
        if 'ginkgo' in lower_species:
            color = 'orange'
        elif is_deciduous:
            if tree_info['fall_colors']:
                color = 'red'
            else:
                color = 'brown'
        else:
            color = 'green'
        color_hex = deterministic_color(species, color_range=color)
        for lat, lng in xys:
            popup = folium.Popup(format_tree_info(species, tree_info), max_width=300)
            # print(x, y)
            folium.CircleMarker((lat, lng), color=color_hex, radius=1, popup=popup, lazy=True).add_to(group_1)
            # folium.CircleMarker(transformer.transform(x, y), color=color, radius=1).add_to(group_1)
        # break
    # folium.Marker((0, 0), icon=folium.Icon("red")).add_to(group_1)
    # folium.Marker((1, 0), icon=folium.Icon("red")).add_to(group_1)

    # group_2 = folium.FeatureGroup("second group").add_to(m)
    # folium.Marker((0, 1), icon=folium.Icon("green")).add_to(group_2)

    folium.LayerControl().add_to(m)

    return m


def build_geojson(top_trees, tree_info_map, center_lat_lng, zoom_level):
    """
    Builds a GeoJSON FeatureCollection for trees with color information.
    
    Args:
        top_trees: A list of tuples, where each tuple contains:
            - species name (str)
            - a list of (latitude, longitude) tuples.
        tree_info_map: Dictionary mapping species names (lowercase) to tree info.
        center_lat_lng: Tuple of (latitude, longitude) for map center (not used but kept for API consistency).
        zoom_level: Zoom level (not used but kept for API consistency).
    
    Returns:
        A GeoJSON FeatureCollection dictionary.
    """
    features = []
    
    for species, xys in top_trees:
        lower_species = species.lower()
        if 'Vacant' in species or 'OBSOLETE' in species or species == 'Stump' or 'unknown' in lower_species:
            print('skipping', species)
            continue
        tree_info = tree_info_map.get(species.lower())
        if tree_info is None:
            tree_info = tree_info_map.get(species.lower().replace(' ', '_'))
        if tree_info is None:
            print(f"No information found for {species}")
            continue
        is_deciduous = tree_info['deciduous']
        
        # Determine color range based on tree characteristics
        if 'ginkgo' in lower_species:
            color = 'orange'
        elif is_deciduous:
            if tree_info['fall_colors']:
                color = 'red'
            else:
                color = 'brown'
        else:
            color = 'green'
        color_hex = deterministic_color(species, color_range=color)
        
        # Create a Point feature for each tree location
        for lat, lng in xys:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]  # GeoJSON uses [longitude, latitude]
                },
                "properties": {
                    "species": species,
                    "color": color_hex,
                    "color_range": color,
                    "deciduous": is_deciduous,
                    "fall_colors": tree_info.get('fall_colors', False),
                    "beautiful_flowers": tree_info.get('beautiful_flowers', False),
                    "blooming_season": tree_info.get('blooming_season', 'N/A'),
                    "common_names": tree_info.get('common_names', []),
                    "chinese_common_names": tree_info.get('chinese_common_names', []),
                    "explanation": tree_info.get('explanation', '')
                }
            }
            features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return geojson


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
    tree_map_all_big = TreeSpeciesMap()
    if os.path.exists(palo_alto_info_file):
        print(f"Loading tree info from {palo_alto_info_file}")
        with open(palo_alto_info_file, 'r') as f:
            tree_map_all_big.species_data = json.load(f)
        print("Tree info loaded.")
    else:
        print("Fetching tree info from API...")
        # Filter out species that are already in tree_map_all_big.species_data
        species_to_fetch = [g[0] for g in groups if g[0].lower() not in tree_map_all_big.species_data]
        tree_map_all_big.add_species_by_list(species_to_fetch)
        tree_map_all_big.save_as_json_file(palo_alto_info_file)
        print(f"Tree info saved to {palo_alto_info_file}")

    # --- Build GeoJSON ---
    print("Building GeoJSON...")
    center_lat_lng, zoom_level = find_center_and_zoom(df, 'LATITUDE', 'LONGITUDE')
    if center_lat_lng:
      geojson_data = build_geojson(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
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

import pandas as pd
import os.path
import json
import pyproj
from pyproj import Transformer
import hashlib
import random
import colorsys


# Define file paths for San Jose data
san_jose_raw_data_file = './Street_Tree_San_Jose.csv'
san_jose_summary_file = './tree_summary_san_jose.json'
san_jose_map_file = './web/san_jose.html'
san_jose_geojson_file = os.path.join(project_root, 'trees_san_jose.geojson')

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

    # --- Build GeoJSON (San Jose) ---
    print("Building San Jose GeoJSON...")
    # Adjust column names if necessary for San Jose data (e.g., 'LATITUDE', 'LONGITUDE')
    center_lat_lng, zoom_level = find_center_and_zoom(sj_pd, 'LATITUDE', 'LONGITUDE')
    if center_lat_lng:
      geojson_data_sj = build_geojson(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
      with open(san_jose_geojson_file, 'w') as f:
          json.dump(geojson_data_sj, f, indent=2)
      print(f"San Jose GeoJSON saved to {san_jose_geojson_file}")
      # --- Build Map (disabled by default) ---
      # m = build_map(groups[:80], tree_map_all_big.species_data, center_lat_lng, zoom_level)
      # m.save(san_jose_map_file)
      # print(f"Map saved to {san_jose_map_file}")
    else:
      print("Could not determine map center and zoom level from data.")

else:
    print("Cannot process empty DataFrame.")