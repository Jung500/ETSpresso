# this_is_fine/views.py

import math
import random
import csv
import folium
import os

from django.shortcuts import render
from django.conf import settings

def fires_map_view(request):
    """
    Single view that handles:
      - "Add Fire": adds 1 new random fire to session
      - "Clear Fires": clears all fires
      - Then builds a Folium map with all fires so far,
        each with 3 distinct hydrants + 1 station.
    """

    # 1) Check user action from GET params
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

    # 2) Load hydrants/stations
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")
    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # 3) Build a Folium map
    center_lat = 45.55  # roughly the center
    center_lon = -73.585
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # bounding box in green
    box_coords = [
        (45.53, -73.62),
        (45.53, -73.55),
        (45.58, -73.55),
        (45.58, -73.62),
        (45.53, -73.62),
    ]
    folium.PolyLine(box_coords, color='green', weight=3).add_to(m)

    # We'll keep track of used hydrants across all fires to keep them distinct
    used_hydrants = set()

    for i, f in enumerate(fires, start=1):
        f_lat, f_lon = f["lat"], f["lon"]

        # Mark the fire (red)
        folium.Marker(
            [f_lat, f_lon],
            icon=folium.Icon(color='red', icon='fire'),
            popup=f"Fire #{i}"
        ).add_to(m)

        # Sort hydrants by distance
        hydrants_dist = []
        for h in hydrants:
            dist_m = haversine_distance(f_lat, f_lon, h["lat"], h["lon"])
            hydrants_dist.append({**h, "dist": dist_m})
        hydrants_dist.sort(key=lambda x: x["dist"])

        # pick 3 distinct
        chosen_h = []
        for h in hydrants_dist:
            hid = (h["lat"], h["lon"])
            if hid not in used_hydrants:
                chosen_h.append(h)
                used_hydrants.add(hid)
                if len(chosen_h) == 3:
                    break

        # place them in blue
        for idx, hh in enumerate(chosen_h, start=1):
            popup_txt = f"<b>Fire #{i} Hydrant {idx}</b><br>Addr: {hh['Address']}"
            folium.Marker(
                [hh["lat"], hh["lon"]],
                icon=folium.Icon(color='blue', icon='tint'),
                popup=popup_txt
            ).add_to(m)

        # 1 nearest station
        best_s = None
        best_dist = float("inf")
        for s in stations:
            ds = haversine_distance(f_lat, f_lon, s["lat"], s["lon"])
            if ds < best_dist:
                best_s = s
                best_dist = ds

        if best_s:
            st_popup = f"<b>Fire #{i} Station</b><br>{best_s['Station']}"
            folium.Marker(
                [best_s["lat"], best_s["lon"]],
                icon=folium.Icon(color='green', icon='home'),
                popup=st_popup
            ).add_to(m)

    # convert map
    map_html = m._repr_html_()

    # render fires_map.html
    return render(request, 'fires_map.html', {"map_html": map_html})

################################################
# Utility Functions (CSV reading, distance, etc.)
################################################

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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
        print("Hydrants CSV not found:", csv_path)
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
        print("Stations CSV not found:", csv_path)
    return stations