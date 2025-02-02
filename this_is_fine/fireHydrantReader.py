import csv
import folium
from folium.plugins import MarkerCluster

def read_hydrant_data(file_path):
    """
    Reads hydrant data from CSV, returns a list of hydrant dicts with:
      'Address', 'Status', 'Abandoned', 'Elevation', etc. plus 'Coordinates'=(lat, lon).
    """
    hydrants = []
    count = 0  # example: only read first 30 if you like

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                lat = float(row["LATITUDE"])
                lon = float(row["LONGITUDE"])
                hydrants.append({
                    "Address": row["\ufeffADRESSE"],
                    "Status": row["STATUT_ACTIF"],
                    "Abandoned": row["ABANDONNE_R"],
                    "Elevation": row["ELEVATION_TERRAIN"],
                    # plus other fields if you want them
                    "Coordinates": (lat, lon),
                })
                count += 1
                if count >= 900:  # remove if you want them all
                    break
            except ValueError:
                print(f"Skipping invalid hydrant row: {row}")

    return hydrants

def create_hydrant_map(hydrants, map_filename="hydrants_map.html"):
    """
    Creates a Folium map with clustered hydrant markers, saves to map_filename.
    """
    if not hydrants:
        print("No hydrants to map!")
        return

    center = hydrants[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    marker_cluster = MarkerCluster(
        options={
            "disableClusteringAtZoom": 16,
            "spiderfyOnMaxZoom": False,
        }
    ).add_to(m)

    for h in hydrants:
        lat, lon = h["Coordinates"]
        popup_html = (
            f"<b>Address:</b> {h['Address']}<br>"
            f"<b>Status:</b> {h['Status']}<br>"
            f"<b>Elevation:</b> {h['Elevation']}<br>"
            f"<b>Abandoned:</b> {h['Abandoned']}"
        )
        color = "red" if (h["Abandoned"] and h["Abandoned"].lower() == "yes") else "blue"
        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            icon=folium.Icon(color=color)
        ).add_to(marker_cluster)

    m.save(map_filename)
    print(f"Hydrant map saved as {map_filename}")