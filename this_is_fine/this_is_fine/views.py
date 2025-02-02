# this_is_fine/this_is_fine/views.py

import os
from django.conf import settings
from django.shortcuts import render
# Import the utility functions you just created:
from ..hydrant_utils import (
    read_hydrant_data,
    read_fire_stations,
    # optional if you want them: create_hydrant_map, create_fire_map
)
import folium

def combined_map_view(request):
    """
    Loads hydrants & fire stations from CSV,
    then builds a Folium map and returns it in the template.
    """
    # Path to your CSVs. Adjust as needed.
    # For example, if 'aqu_borneincendie_p.csv' is in the same folder as manage.py:
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")

    # Read data
    hydrants = read_hydrant_data(hydrants_csv)
    stations = read_fire_stations(stations_csv)

    # Build a Folium map in-memory (rather than saving to file)
    if hydrants:
        center_lat, center_lon = hydrants[0]["Coordinates"]
    elif stations:
        center_lat, center_lon = stations[0]["Coordinates"]
    else:
        # fallback
        center_lat, center_lon = (45.5017, -73.5673)  # Montreal approx

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Add hydrants (blue)
    for h in hydrants:
        lat, lon = h["Coordinates"]
        folium.Marker(
            [lat, lon],
            popup=(
                f"<b>Hydrant Address:</b> {h['Address']}<br>"
                f"<b>Status:</b> {h['Status']}"
            ),
            icon=folium.Icon(color="blue", icon="tint")
        ).add_to(m)

    # Add stations (red)
    for s in stations:
        lat, lon = s["Coordinates"]
        folium.Marker(
            [lat, lon],
            popup=(
                f"<b>Station:</b> {s['Station']}<br>"
                f"<b>Address:</b> {s['Address']}"
            ),
            icon=folium.Icon(color="red", icon="fire")
        ).add_to(m)

    # Convert map to HTML
    map_html = m._repr_html_()

    # Render a template called 'map.html' and pass map_html
    return render(request, 'map.html', {"map_html": map_html})