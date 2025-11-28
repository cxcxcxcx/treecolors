import hashlib
import random
import colorsys
import os.path
import json

# Define file paths
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)


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
        new_species = [s.lower() for s in species_list if s and s.lower() not in self.species_data and s.lower().replace(' ', '_') not in self.species_data]
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


def load_shared_tree_info(additional_species=None):
    """
    Loads or creates the shared tree information map from the Palo Alto tree info file.
    This function ensures tree_map_all_big is shared across all scripts.
    
    Args:
        additional_species: Optional list of species to fetch if not in the file.
    
    Returns:
        TreeSpeciesMap instance with loaded species data.
    """
    shared_info_file = os.path.join(project_root, 'tree_info_palo_alto_1000_gpt4o.json')
    tree_map = TreeSpeciesMap()
    
    if os.path.exists(shared_info_file):
        print(f"Loading shared tree info from {shared_info_file}")
        with open(shared_info_file, 'r') as f:
            tree_map.species_data = json.load(f)
        print("Shared tree info loaded.")
    else:
        print(f"Shared tree info file not found at {shared_info_file}.")
        tree_map.species_data = {}
    
    # If additional species are provided and not in the map, fetch them
    if additional_species:
        species_to_fetch = [s for s in additional_species 
                          if s and s.lower() not in tree_map.species_data 
                          and s.lower().replace(' ', '_') not in tree_map.species_data]
        if species_to_fetch:
            print(f"Fetching {len(species_to_fetch)} additional species...")
            tree_map.add_species_by_list(species_to_fetch)
            # Save updated tree info
            with open(shared_info_file, 'w') as f:
                json.dump(tree_map.species_data, f, indent=4)
            print(f"Updated tree info saved to {shared_info_file}")
    
    return tree_map

# Shared tree_map_all_big instance - loaded on first access
_tree_map_all_big = None

def get_shared_tree_map(additional_species=None):
    """
    Gets the shared tree_map_all_big instance, loading it if necessary.
    
    Args:
        additional_species: Optional list of species to fetch if not in the file.
    
    Returns:
        TreeSpeciesMap instance with loaded species data.
    """
    global _tree_map_all_big
    if _tree_map_all_big is None:
        _tree_map_all_big = load_shared_tree_info(additional_species)
    elif additional_species:
        # Check if any new species need to be fetched
        species_to_fetch = [s for s in additional_species 
                          if s and s.lower() not in _tree_map_all_big.species_data 
                          and s.lower().replace(' ', '_') not in _tree_map_all_big.species_data]
        if species_to_fetch:
            print(f"Fetching {len(species_to_fetch)} additional species...")
            _tree_map_all_big.add_species_by_list(species_to_fetch)
            # Save updated tree info
            shared_info_file = os.path.join(project_root, 'tree_info_palo_alto_1000_gpt4o.json')
            with open(shared_info_file, 'w') as f:
                json.dump(_tree_map_all_big.species_data, f, indent=4)
            print(f"Updated tree info saved to {shared_info_file}")
    return _tree_map_all_big


def build_geojson(top_trees, tree_info_map):
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
        if 'deciduous' not in tree_info:
            print(f"No deciduous information found for {species}")
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