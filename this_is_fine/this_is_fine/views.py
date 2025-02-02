# this_is_fine/views.py

import requests
import math
import random
import csv
import os
import folium

from django.shortcuts import render
from django.conf import settings

def fires_map_view(request):
    """
    Single route:
     - 'Add Fire': add one random fire to session
     - 'Clear Fires': remove all
     - Then build map with all fires: each has nearest station + 3 hydrants + OSRM routes (blue).
    """

    # 1) Parse ?action=add or ?action=clear
    action = request.GET.get('action')
    fires = request.session.get('fires', [])

    if action == 'clear':
        fires = []
    elif action == 'add':
        # bounding box near Rosemont
        MIN_LAT, MAX_LAT = 45.53, 45.58
        MIN_LON, MAX_LON = -73.62, -73.55

        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)
        fires.append({"lat": lat, "lon": lon})

    # Update session
    request.session['fires'] = fires

    # 2) Read hydrants/stations
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")
    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # 3) Create Folium map
    center_lat, center_lon = 45.55, -73.58
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # bounding box (green)
    box_coords = [
        (45.53, -73.62),
        (45.53, -73.55),
        (45.58, -73.55),
        (45.58, -73.62),
        (45.53, -73.62),
    ]
    folium.PolyLine(box_coords, color='green', weight=3).add_to(m)

    # We'll track used_hydrants if you want them distinct across all fires, but you didn't specify.
    # So let's skip distinct logic. We'll just find 3 nearest hydrants for each fire.

    # For each fire in session
    for i, f in enumerate(fires, start=1):
        f_lat, f_lon = f["lat"], f["lon"]

        # Mark the fire (red)
        folium.Marker(
            [f_lat, f_lon],
            icon=folium.Icon(color='red', icon='fire'),
            popup=f"Fire #{i}"
        ).add_to(m)

        # 1) nearest station
        best_station = None
        best_dist = float('inf')
        for s in stations:
            d = haversine_distance(f_lat, f_lon, s["lat"], s["lon"])
            if d < best_dist:
                best_station = s
                best_dist = d

        if best_station:
            # Mark station (green)
            folium.Marker(
                [best_station["lat"], best_station["lon"]],
                icon=folium.Icon(color='green', icon='home'),
                popup=f"Station for Fire #{i}"
            ).add_to(m)

        # 2) find 3 nearest hydrants
        hydrants_dist = []
        for h in hydrants:
            d = haversine_distance(f_lat, f_lon, h["lat"], h["lon"])
            hydrants_dist.append({**h, "dist": d})
        hydrants_dist.sort(key=lambda x: x["dist"])

        # pick top 3
        chosen_3 = hydrants_dist[:3]
        for h_idx, h in enumerate(chosen_3, start=1):
            # Mark hydrant (blue)
            folium.Marker(
                [h["lat"], h["lon"]],
                icon=folium.Icon(color='blue', icon='tint'),
                popup=f"Fire #{i} Hydrant #{h_idx}"
            ).add_to(m)

            # 3) add OSRM route from station -> each hydrant, in blue
            if best_station:
                add_osrm_route_osm(m, best_station, h, color="blue")

    # Convert to HTML
    map_html = m._repr_html_()

    return render(request, 'fires_map.html', {"map_html": map_html})


############################
# Utility: reading CSV + distance
############################

def read_hydrants(csv_path):
    hydrants = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row["LATITUDE"])
                    lon = float(row["LONGITUDE"])
                    hydrants.append({
                        "Address": row.get("\ufeffADRESSE",""),
                        "lat": lat,
                        "lon": lon
                    })
                except ValueError:
                    pass
    except FileNotFoundError:
        print("Hydrants CSV missing:", csv_path)
    return hydrants

def read_stations(csv_path):
    stations = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row["LATITUDE"])
                    lon = float(row["LONGITUDE"])
                    stations.append({
                        "Station": row.get("CASERNE",""),
                        "lat": lat,
                        "lon": lon
                    })
                except ValueError:
                    pass
    except FileNotFoundError:
        print("Stations CSV missing:", csv_path)
    return stations

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    import math
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def add_osrm_route_osm(m, station, hydrant, color="blue"):
    """
    Calls the OSRM public endpoint to get fastest driving route 
    from 'station' -> 'hydrant'. Then draws a polyline in the given 'color'.
    """
    s_lat, s_lon = station["lat"], station["lon"]
    h_lat, h_lon = hydrant["lat"], hydrant["lon"]

    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{s_lon},{s_lat};{h_lon},{h_lat}"
           f"?overview=full&geometries=geojson")

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("code") == "Ok":
            route_coords = data["routes"][0]["geometry"]["coordinates"]  # list of [lon, lat]
            # invert to [lat, lon]
            folium_coords = [(c[1], c[0]) for c in route_coords]

            folium.PolyLine(
                locations=folium_coords,
                color=color,
                weight=4,
                opacity=0.8
            ).add_to(m)
        else:
            print("OSRM route error:", data.get("code"))
    except requests.exceptions.RequestException as e:
        print("OSRM request failed:", e)