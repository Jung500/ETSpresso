import csv
import folium
import random
import math
import os

#########################
# 1) CSV READING FUNCTIONS
#########################

def read_hydrants(csv_path):
    """Load hydrants from aqu_borneincendie_p.csv. Returns list of dicts with lat/lon."""
    hydrants = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
                hydrants.append({
                    "Address": row.get("\ufeffADRESSE") or row.get("ADRESSE", ""),
                    "Status": row.get("STATUT_ACTIF", ""),
                    "Abandoned": row.get("ABANDONNE_R", ""),
                    "Elevation": row.get("ELEVATION_TERRAIN", ""),
                    "lat": lat,
                    "lon": lon
                })
            except ValueError:
                pass
    return hydrants

def read_stations(csv_path):
    """Load fire stations from casernes.csv. Returns list of dicts with lat/lon."""
    stations = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
                stations.append({
                    "Station": row.get("CASERNE", ""),
                    "Address": f"{row.get('NO_CIVIQUE','')} {row.get('RUE','')}",
                    "Arrondissement": row.get("ARRONDISSEMENT", ""),
                    "lat": lat,
                    "lon": lon
                })
            except ValueError:
                pass
    return stations

#########################
# 2) HELPER FUNCTIONS
#########################

def distance_haversine(lat1, lon1, lat2, lon2):
    """
    Returns approximate distance in meters between two lat/lon points 
    using the Haversine formula.
    """
    R = 6371000  # Earth radius in meters
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_random_fires(n=5):
    """
    Generate n random 'fires' in a bigger bounding box across Montreal.
    
    Tweak these corners to enlarge/center the box on land:
    e.g. lat ~ [45.40, 45.60], lon ~ [-73.75, -73.50].
    """
    MIN_LAT, MAX_LAT = 45.40, 45.60
    MIN_LON, MAX_LON = -73.75, -73.50

    fires = []
    for _ in range(n):
        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)
        fires.append({"lat": lat, "lon": lon})
    return fires, [(MIN_LAT, MIN_LON), (MIN_LAT, MAX_LON), 
                   (MAX_LAT, MAX_LON), (MAX_LAT, MIN_LON)]

#########################
# 3) MAIN: COMBINE MAP
#########################

def create_combined_map(num_fires=5, hydrant_csv="aqu_borneincendie_p.csv", 
                        station_csv="casernes.csv", outfile="combined_map.html"):
    """
    1) Loads hydrants & stations from CSV.
    2) Generates multiple random fires inside a bounding box.
    3) For each fire, pick 3 distinct hydrants & (optionally) 1 station.
    4) Plot them on a single Folium map, including the bounding box.
    """
    # Read data
    hydrants = read_hydrants(hydrant_csv)
    stations = read_stations(station_csv)

    # Generate random fires and bounding box corners
    fires, box_corners = generate_random_fires(n=num_fires)

    # Create Folium map. Use a middle point of the bounding box as a guess:
    center_lat = (box_corners[0][0] + box_corners[2][0]) / 2
    center_lon = (box_corners[0][1] + box_corners[1][1]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

    # Draw bounding box on the map
    folium.PolyLine(
        locations=box_corners + [box_corners[0]],  # close polygon
        color='green', weight=3, opacity=0.8
    ).add_to(m)

    # We'll keep track of hydrants we've used, so each hydrant is assigned to only one fire:
    used_hydrant_ids = set()

    # For each fire, find 3 nearest hydrants (not yet used), plus 1 nearest station
    for i, fire in enumerate(fires, start=1):
        f_lat, f_lon = fire["lat"], fire["lon"]

        # Mark the fire (red)
        folium.Marker(
            [f_lat, f_lon],
            icon=folium.Icon(color='red', icon='fire'),
            popup=f"Fire #{i}"
        ).add_to(m)

        # Sort hydrants by distance, pick first 3 that are unused
        sorted_hyd = []
        for h in hydrants:
            d = distance_haversine(f_lat, f_lon, h["lat"], h["lon"])
            # copy h so we can store dist
            hydrant_copy = dict(h)
            hydrant_copy["dist"] = d
            sorted_hyd.append(hydrant_copy)
        sorted_hyd.sort(key=lambda x: x["dist"])

        nearest_hydrants = []
        for h in sorted_hyd:
            coord_id = (h["lat"], h["lon"])
            if coord_id not in used_hydrant_ids:
                nearest_hydrants.append(h)
                used_hydrant_ids.add(coord_id)
                if len(nearest_hydrants) == 3:
                    break

        # Plot these hydrants (blue)
        for idx, h in enumerate(nearest_hydrants, start=1):
            pop = (f"<b>Fire #{i} Hydrant #{idx}</b><br>Address: {h['Address']}")
            folium.Marker(
                [h["lat"], h["lon"]],
                icon=folium.Icon(color="blue", icon="tint"),
                popup=pop
            ).add_to(m)

        # Find 1 nearest station (green). No uniqueness required
        if stations:
            best_station = None
            best_dist = float("inf")
            for s in stations:
                dist_s = distance_haversine(f_lat, f_lon, s["lat"], s["lon"])
                if dist_s < best_dist:
                    best_station = s
                    best_dist = dist_s
            if best_station:
                station_pop = (f"<b>Fire #{i} Nearest Station</b><br>"
                               f"Station: {best_station['Station']}")
                folium.Marker(
                    [best_station["lat"], best_station["lon"]],
                    icon=folium.Icon(color="green", icon="home"),
                    popup=station_pop
                ).add_to(m)

    # Finally, save the map
    m.save(outfile)
    print(f"Combined map saved as {outfile}")


###############
# DRIVER CODE
###############

if __name__ == "__main__":
    # CSV filenames in the same folder
    hydrant_csv = "aqu_borneincendie_p.csv"
    station_csv = "casernes.csv"

    # Create a single map showing e.g. 5 fires, each with 3 hydrants + 1 station
    create_combined_map(
        num_fires=5,
        hydrant_csv=hydrant_csv,
        station_csv=station_csv,
        outfile="combined_map.html"
    )