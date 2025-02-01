import csv
import folium

def read_fire_stations(file_path):
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
                    "Start Date": row["DATE_DEBUT"],
                    "End Date": row["DATE_FIN"],
                    "Coordinates": (lat, lon)
                })
            except ValueError:
                print(f"Skipping invalid row: {row}")  # Handle missing or invalid data
                
    return fire_stations

def create_fire_map(hydrants, fire_stations, map_filename="fire_map.html"):
    if not hydrants and not fire_stations:
        print("No locations to map!")
        return
    
    # Center the map around the first fire station or hydrant
    center = hydrants[0]["Coordinates"] if hydrants else fire_stations[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    # Add Fire Hydrants (blue markers)
    for hydrant in hydrants:
        lat, lon = hydrant["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=f"""
            <b>Hydrant Address:</b> {hydrant['Address']}<br>
            <b>Status:</b> {hydrant['Status']}<br>
            <b>Elevation:</b> {hydrant['Elevation']}<br>
            <b>Abandoned:</b> {hydrant['Abandoned']}
            """,
            icon=folium.Icon(color="blue", icon="tint")
        ).add_to(m)

    # Add Fire Stations (red markers)
    for station in fire_stations:
        lat, lon = station["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=f"""
            <b>Fire Station:</b> {station['Station']}<br>
            <b>Address:</b> {station['Address']}<br>
            <b>City:</b> {station['City']}<br>
            <b>Arrondissement:</b> {station['Arrondissement']}
            """,
            icon=folium.Icon(color="red", icon="fire")
        ).add_to(m)

    # Save the updated map
    m.save(map_filename)
    print(f"Map saved as {map_filename}")
    