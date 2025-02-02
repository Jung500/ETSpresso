import csv
import folium
from folium.plugins import MarkerCluster

def read_hydrant_data(file_path):
    hydrants = []
    count = 0  # Counter to track the number of hydrants processed

    # Open and read the file
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)  # Reads file as a dictionary with column headers as keys
        
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
                if count >= 30:
                    break  # Only process the first 30 hydrants
            except ValueError:
                print(f"Skipping invalid row: {row}")  # Handle missing or invalid data
                
    return hydrants


# Function to create and save a Folium map with clustering
def create_hydrant_map(hydrants, map_filename="hydrants_map.html"):
    if not hydrants:
        print("No hydrants to map!")
        return

    # Define the base map centered on the first hydrant
    center = hydrants[0]["Coordinates"]
    m = folium.Map(location=center, zoom_start=12)

    # Create a MarkerCluster with custom options
    marker_cluster = MarkerCluster(
        options={
            # When zoomed in beyond this level, clustering is disabled so individual markers show
            "disableClusteringAtZoom": 16,
            # You can also adjust other options such as spiderfy on max zoom
            "spiderfyOnMaxZoom": False,
        }
    ).add_to(m)

    # Add each hydrant marker to the marker cluster
    for hydrant in hydrants:
        lat, lon = hydrant["Coordinates"]
        folium.Marker(
            location=[lat, lon],
            popup=f"""
            <b>Address:</b> {hydrant['Address']}<br>
            <b>Status:</b> {hydrant['Status']}<br>
            <b>Elevation:</b> {hydrant['Elevation']}<br>
            <b>Abandoned:</b> {hydrant['Abandoned']}
            """,
            icon=folium.Icon(color="red" if hydrant["Abandoned"].lower() == "yes" else "blue")
        ).add_to(marker_cluster)

    # Save the map only once
    m.save(map_filename)
    print(f"Map saved as {map_filename}")
