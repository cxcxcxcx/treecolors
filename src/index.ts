import * as L from 'leaflet';

interface Tree {
    deciduous: boolean;
    fall_colors: boolean;
    beautiful_flowers: boolean;
    blooming_season: string;
    chinese_common_names: string[];
    common_names: string[];
    explanation: string;
    species: string;
    color: string;
}
type TreeDict = { [species: string]: Tree };

interface Location {
    lat: number;
    lng: number;
}

interface TreeLocation {
    species: string;
    locations: Location[];
}

async function fetchTreeData(): Promise<{ treeDict: TreeDict; treeLocations: TreeLocation[] }> {
    const treeResponse = await fetch('tree_info_palo_alto_flattened.json');
    const treeData: Tree[] = await treeResponse.json();
    const treeDict: TreeDict = {};
    console.log('treeData', treeData);
    treeData.forEach((tree) => {
      treeDict[tree.species.toLowerCase()] = tree;
    });
    const treeLocationResponse = await fetch('tree_summary_palo_alto.json');
    const treeLocationData: TreeLocation[] = await treeLocationResponse.json();

    return { treeDict, treeLocations: treeLocationData };
}

function calculateMapBounds(treeLocations: TreeLocation[]): { center: [number, number]; zoom: number } {
    console.log('treeLocations', treeLocations);
    const latitudes = treeLocations.flatMap((location) => location.locations.map((loc) => loc.lat));
    const longitudes = treeLocations.flatMap((location) => location.locations.map((loc) => loc.lng));
  
    const minLatitude = Math.min(...latitudes);
    const maxLatitude = Math.max(...latitudes);
    const minLongitude = Math.min(...longitudes);
    const maxLongitude = Math.max(...longitudes);
  
    const centerLatitude = (minLatitude + maxLatitude) / 2;
    const centerLongitude = (minLongitude + maxLongitude) / 2;
  
    const latitudeRange = maxLatitude - minLatitude;
    const longitudeRange = maxLongitude - minLongitude;
  
    const zoom = Math.floor(Math.log2(360 / Math.max(latitudeRange, longitudeRange)));
  
    return { center: [centerLatitude, centerLongitude], zoom };
  }

async function createLeafletMap(treeDict: TreeDict, treeLocationData: TreeLocation[]): Promise<void> {
    const { center, zoom } = calculateMapBounds(treeLocationData);
    const map = L.map('map').setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);

    treeLocationData.forEach(({species, locations}) => {
        const lowerSpecies = species.toLowerCase();
        if (species.includes('Vacant') || species.includes('OBSOLETE') || species === 'Stump' || lowerSpecies.includes('unknown')) {
          console.log(`skipping ${species}`);
          return;
        }
        const tree = treeDict[lowerSpecies];
        // console.log('tree', species, tree);
        if (tree === undefined) {
            console.log(`skipping ${species}`);
            return;
        }
        locations.forEach(({ lat, lng }) => {
            const marker = L.circle([lat, lng], {
                color: tree.color,
                // fillColor: 'red',
                // fillOpacity: 0.6,
                radius: 1,
            });
            marker.addTo(map);
        });
    });
}

async function main() {
    const { treeDict, treeLocations } = await fetchTreeData();
    console.log(treeDict);
    createLeafletMap(treeDict, treeLocations);
}
main();
console.log("hello world");