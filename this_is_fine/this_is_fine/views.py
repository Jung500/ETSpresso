# this_is_fine/views.py

import os
import math
import random
import csv
import requests
import joblib

from django.shortcuts import render
from django.conf import settings
from datetime import datetime
import folium


#######################################
# 1) Load the ML model at module level
#######################################
MODEL_PATH = os.path.join(settings.BASE_DIR, "severity_model.pkl")
severity_model = joblib.load(MODEL_PATH)


#######################################
# 2) Utility Functions
#######################################

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
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def add_osrm_route(m, station, hydrant):
    """
    Calls OSRM to get station->hydrant route, draws a blue line on the Folium map.
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
            coords = data["routes"][0]["geometry"]["coordinates"]  # list of [lon,lat]
            folium_coords = [(c[1], c[0]) for c in coords]          # invert to [lat,lon]
            folium.PolyLine(
                locations=folium_coords,
                color="blue",
                weight=4,
                opacity=0.8
            ).add_to(m)
        else:
            print("OSRM route error:", data.get("code"))
    except requests.exceptions.RequestException as e:
        print("OSRM request failed:", e)


#######################################
# 3) The Main View with 1-Station-per-2-Fires logic
#######################################

def fires_map_view(request):
    """
    A refresh-based approach:
      - ?action=add => add 1 random fire to session
      - ?action=clear => remove all fires
    We only assign 1 station for every 2 fires:
      - The first fire of a pair picks a new station
      - The second fire of that pair reuses the same station
    We also pick 3 hydrants for each fire, do OSRM routes, 
    and color the fire marker based on ML-predicted severity (low/med/high).
    """

    # 1) handle user actions
    action = request.GET.get('action')
    fires = request.session.get('fires', [])
    # we'll also store 'pair_count' to handle station picking
    # for each pair of fires, we pick a new station
    pair_count = request.session.get('pair_count', 0)

    if action == 'clear':
        fires = []
        pair_count = 0
    elif action == 'add':
        # bounding box near Rosemont
        MIN_LAT, MAX_LAT = 45.53, 45.58
        MIN_LON, MAX_LON = -73.62, -73.55

        f_lat = random.uniform(MIN_LAT, MAX_LAT)
        f_lon = random.uniform(MIN_LON, MAX_LON)

        # store new fire
        fires.append({"lat": f_lat, "lon": f_lon})
    # update session
    request.session['fires'] = fires
    request.session['pair_count'] = pair_count

    # 2) load CSV data
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")
    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # 3) create Folium map
    m = folium.Map(location=[45.55, -73.58], zoom_start=13)

    # bounding box in green
    box_coords = [
        (45.53, -73.62),
        (45.53, -73.55),
        (45.58, -73.55),
        (45.58, -73.62),
        (45.53, -73.62),
    ]
    folium.PolyLine(box_coords, color='green', weight=3).add_to(m)

    # We'll pick stations in pairs: for every 2 fires, 1 station.
    # Approach:
    # - We'll loop over the fires in increments of 2
    # - For the first fire in that pair, find nearest station
    # - For the second fire, reuse that station

    # chunk fires in pairs
    pair_of_fires = []
    for i in range(0, len(fires), 2):
        chunk = fires[i:i+2]  # up to 2 fires
        pair_of_fires.append(chunk)

    # For each chunk (1 or 2 fires),
    # we pick the station for the first fire, second fire reuses it
    chunk_index = 0
    for chunk in pair_of_fires:
        chunk_index += 1

        # The "leading" fire = chunk[0]
        main_fire = chunk[0]

        # find nearest station for that main_fire
        best_station = None
        best_dist = float("inf")
        for s in stations:
            d_s = haversine_distance(main_fire["lat"], main_fire["lon"], s["lat"], s["lon"])
            if d_s < best_dist:
                best_station = s
                best_dist = d_s

        # now we have a station for this chunk
        # process each fire in chunk (1 or 2)
        for idx_in_chunk, single_fire in enumerate(chunk, start=1):
            # pick 3 hydrants
            hydrants_dist = []
            for h in hydrants:
                dh = haversine_distance(single_fire["lat"], single_fire["lon"], h["lat"], h["lon"])
                hydrants_dist.append({**h, "dist": dh})
            hydrants_dist.sort(key=lambda x: x["dist"])
            top3 = hydrants_dist[:3]

            # compute severity with the ML model
            # features: [lat, lon, dist_station, time_of_day]
            from datetime import datetime
            now_hour = datetime.now().hour
            station_dist = haversine_distance(single_fire["lat"], single_fire["lon"], best_station["lat"], best_station["lon"]) if best_station else 0
            severity = severity_model.predict([[single_fire["lat"], single_fire["lon"], station_dist, now_hour]])[0]

            color_map = {
                "low": "green",
                "medium": "orange",
                "high": "red"
            }
            fire_color = color_map.get(severity, "red")

            # Mark the fire (with ML severity color)
            folium.Marker(
                [single_fire["lat"], single_fire["lon"]],
                icon=folium.Icon(color=fire_color, icon='fire'),
                popup=f"Fire => severity={severity}"
            ).add_to(m)

            # Mark station in green if we have it
            if best_station and idx_in_chunk == 1:
                # place the station marker only for the first fire in chunk 
                # (to avoid repeated station marker)
                folium.Marker(
                    [best_station["lat"], best_station["lon"]],
                    icon=folium.Icon(color='green', icon='home'),
                    popup=f"Station for chunk {chunk_index}"
                ).add_to(m)

            # Mark 3 hydrants in blue + OSRM route for each
            if best_station:
                for hid_idx, hydr in enumerate(top3, start=1):
                    folium.Marker(
                        [hydr["lat"], hydr["lon"]],
                        icon=folium.Icon(color='blue', icon='tint'),
                        popup=f"Hydrant #{hid_idx}"
                    ).add_to(m)

                    # add route station->hydr
                    add_osrm_route(m, best_station, hydr)

    # finalize map
    map_html = m._repr_html_()
    return render(request, 'fires_map.html', {"map_html": map_html})