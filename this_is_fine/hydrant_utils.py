# this_is_fine/hydrant_utils.py

import csv
import folium
from folium.plugins import MarkerCluster

def read_hydrant_data(file_path):
    """
    Reads hydrant data from CSV, returns a list of hydrant dicts.
    Each dict has: Address, Jurisdiction, Owner, Status, etc., plus Coordinates=(lat, lon).
    """
    hydrants = []
    count = 0  # Example: limit to first 30 hydrants

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
                hydrants.append({
                    "Address": row["\ufeffADRESSE"],
                    "Jurisdiction": row["JURIDICTION"],
                    "Owner": row["PROPRIETAIRE"],
                    "Installation Date": row["DATE_INSTALLATION"],
                    "Status": row["STATUT_ACTIF"],
                    "Abandoned": row["ABANDONNE_R"],
                    "Elevation": row["ELEVATION_TERRAIN"],
                    "Coordinates": (lat, lon)
                })
                count += 1
                if count >= 30:  # Example cap
                    break
            except ValueError:
                print(f"Skipping invalid row: {row}")

    return hydrants


def create_hydrant_map(hydrants, map_filename="hydrants_map.html"):
    """
    Given a list of hydrant dicts, creates a Folium map with clustering, 
    then saves to map_filename.
    """
    if not hydrants:
        print("No hydrants to map!")
        return

    # Center map on first hydrant
    center = hydrants[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    # Marker cluster
    marker_cluster = MarkerCluster(
        options={
            "disableClusteringAtZoom": 16,
            "spiderfyOnMaxZoom": False,
        }
    ).add_to(m)

    # Add hydrants to cluster
    for hydrant in hydrants:
        lat, lon = hydrant["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=(
                f"<b>Address:</b> {hydrant['Address']}<br>"
                f"<b>Status:</b> {hydrant['Status']}<br>"
                f"<b>Elevation:</b> {hydrant['Elevation']}<br>"
                f"<b>Abandoned:</b> {hydrant['Abandoned']}"
            ),
            icon=folium.Icon(
                color="red" if hydrant["Abandoned"].lower() == "yes" else "blue"
            )
        ).add_to(marker_cluster)

    m.save(map_filename)
    print(f"Map saved as {map_filename}")


def read_fire_stations(file_path):
    """
    Reads fire station data from CSV, returns a list of dicts with Station, Address, City, etc.
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
                    "Start Date": row["DATE_DEBUT"],
                    "End Date": row["DATE_FIN"],
                    "Coordinates": (lat, lon),
                })
            except ValueError:
                print(f"Skipping invalid row: {row}")
    return fire_stations


def create_fire_map(hydrants, fire_stations, map_filename="fire_map.html"):
    """
    Creates a Folium map of hydrants (blue) and fire stations (red) 
    and saves to map_filename.
    """
    if not hydrants and not fire_stations:
        print("No locations to map!")
        return

    # Center around first hydrant or station
    center = hydrants[0]["Coordinates"] if hydrants else fire_stations[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    # Add hydrants
    for hydrant in hydrants:
        lat, lon = hydrant["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=(
                f"<b>Hydrant Address:</b> {hydrant['Address']}<br>"
                f"<b>Status:</b> {hydrant['Status']}<br>"
                f"<b>Elevation:</b> {hydrant['Elevation']}<br>"
                f"<b>Abandoned:</b> {hydrant['Abandoned']}"
            ),
            icon=folium.Icon(color="blue", icon="tint")
        ).add_to(m)

    # Add fire stations
    for station in fire_stations:
        lat, lon = station["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=(
                f"<b>Fire Station:</b> {station['Station']}<br>"
                f"<b>Address:</b> {station['Address']}<br>"
                f"<b>City:</b> {station['City']}<br>"
                f"<b>Arrondissement:</b> {station['Arrondissement']}"
            ),
            icon=folium.Icon(color="red", icon="fire")
        ).add_to(m)

    m.save(map_filename)
    print(f"Map saved as {map_filename}")