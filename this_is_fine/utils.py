import folium
import csv
import random

def create_fire_map(hydrants, fire_stations, map_filename="fire_map.html"):
    fireStation_icon = folium.CustomIcon("FireStation.png", icon_size=(30, 30))
    hydrant_icon = folium.CustomIcon("FireHydrantLogo.png", icon_size=(30, 30))

    if not hydrants and not fire_stations:
        print("No locations to map!")
        return
    
    # Center the map around the first fire station or hydrant
    center = hydrants[0]["Coordinates"] if hydrants else fire_stations[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    # 🔹 Define the Square Bounding Box (inside Montreal)
    square_bounds = [
        [45.5500, -73.7000],  # Northwest
        [45.5500, -73.5000],  # Northeast
        [45.4500, -73.5000],  # Southeast
        [45.4500, -73.7000],  # Southwest
        [45.5500, -73.7000]   # Close the square
    ]

    # 🔹 Overlay the bounding box on the map
    folium.PolyLine(
        square_bounds, 
        color="red", 
        weight=3, 
        popup="Fire Zone"
    ).add_to(m)

    # 🔥 Generate a random fire location inside the square
    random_lat = round(random.uniform(45.4500, 45.5500), 6)
    random_lon = round(random.uniform(-73.7000, -73.5000), 6)

    # 🔥 Add the fire marker
    folium.Marker(
        location=[random_lat, random_lon], 
        popup="🔥 Random Fire",
        icon=folium.Icon(color="red", icon="fire", prefix="fa")
    ).add_to(m)

    # 🔹 Add Fire Hydrants (blue markers)
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
            icon=hydrant_icon
        ).add_to(m)

    # 🔹 Add Fire Stations (red markers)
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
            icon=fireStation_icon
        ).add_to(m)

    # 🔹 Save the updated map
    m.save(f"maps/static/{map_filename}")
    print(f"Map saved as maps/static/{map_filename}")