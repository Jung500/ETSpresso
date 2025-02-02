import csv
import folium

def read_fire_stations(file_path):
    """
    Reads fire station data from CSV, returns a list of station dicts:
      'Station', 'Address', 'City', 'Arrondissement', plus 'Coordinates'=(lat, lon).
    """
    fire_stations = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
                fire_stations.append({
                    "Station": row["CASERNE"],
                    "Address": f"{row['NO_CIVIQUE']} {row['RUE']}",
                    "City": row["VILLE"],
                    "Arrondissement": row["ARRONDISSEMENT"],
                    "Coordinates": (lat, lon),
                })
            except ValueError:
                print(f"Skipping invalid station row: {row}")
    return fire_stations

def create_fire_map(hydrants, fire_stations, map_filename="fire_map.html"):
    """
    Creates a Folium map showing:
    - Blue markers for hydrants
    - Red markers for fire stations
    Saves to 'fire_map.html' by default.
    """
    if not hydrants and not fire_stations:
        print("No locations to map!")
        return

    if hydrants:
        center = hydrants[0]["Coordinates"]
    else:
        center = fire_stations[0]["Coordinates"]

    m = folium.Map(location=center, zoom_start=12)

    # Add hydrants (blue)
    for h in hydrants:
        lat, lon = h["Coordinates"]
        popup_html = (
            f"<b>Hydrant Address:</b> {h['Address']}<br>"
            f"<b>Status:</b> {h['Status']}<br>"
            f"<b>Elevation:</b> {h['Elevation']}<br>"
            f"<b>Abandoned:</b> {h['Abandoned']}"
        )
        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            icon=folium.Icon(color="blue", icon="tint")
        ).add_to(m)

    # Add fire stations (red)
    for s in fire_stations:
        lat, lon = s["Coordinates"]
        popup_html = (
            f"<b>Fire Station:</b> {s['Station']}<br>"
            f"<b>Address:</b> {s['Address']}<br>"
            f"<b>City:</b> {s['City']}<br>"
            f"<b>Arrondissement:</b> {s['Arrondissement']}"
        )
        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            icon=folium.Icon(color="red", icon="fire")
        ).add_to(m)

    m.save(map_filename)
    print(f"Fire map saved as {map_filename}")