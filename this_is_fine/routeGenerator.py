import requests
import folium
import polyline
from django.conf import settings

# 🔹 Use Django settings for API Key
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY

def generate_route_map(start_location, destination_location):
    """ Generates a Folium map with the fastest route using Google Directions API. """

    # 🔹 Google Directions API URL
    directions_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_location}&destination={destination_location}&mode=driving&key={GOOGLE_MAPS_API_KEY}"

    # 🔹 Request Route Data from Google API
    response = requests.get(directions_url)
    data = response.json()

    # 🔹 Extract Route Polyline Points
    if data["status"] == "OK":
        route = data["routes"][0]["overview_polyline"]["points"]
        decoded_route = polyline.decode(route)  # Convert to list of lat/lon points
    else:
        print("Error fetching directions:", data["status"])
        return None

    # 🔹 Create Folium Map Centered at Start Location
    m = folium.Map(location=[float(start_location.split(',')[0]), float(start_location.split(',')[1])], zoom_start=14)

    # 🔹 Add Start and End Markers
    folium.Marker([float(start_location.split(',')[0]), float(start_location.split(',')[1])],
                  popup="Start", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([float(destination_location.split(',')[0]), float(destination_location.split(',')[1])],
                  popup="Destination", icon=folium.Icon(color="red")).add_to(m)

    # 🔹 Draw the Route on the Map
    folium.PolyLine(decoded_route, color="blue", weight=5, opacity=0.7).add_to(m)

    # 🔹 Save the map as an HTML file
    map_path = "myapp/static/route_map.html"
    m.save(map_path)

    return map_path