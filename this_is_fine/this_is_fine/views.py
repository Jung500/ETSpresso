# this_is_fine/views.py

import os
import random
import math
import csv
import requests
import folium
import joblib  # for loading the scikit-learn model
from django.conf import settings
from django.shortcuts import render

##########################
# 1) Load ML Model at module-level
##########################

MODEL_PATH = os.path.join(settings.BASE_DIR, "severity_model.pkl")
severity_model = joblib.load(MODEL_PATH)  # Contains our random forest

##########################
# 2) Utility: CSV reading + distance
##########################

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
        print("Missing hydrants CSV:", csv_path)
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
        print("Missing stations CSV:", csv_path)
    return stations

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    import math
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def add_osrm_route(m, station, hydrant):
    """
    OSRM route from station -> hydrant, color in BLUE.
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
            coords = data["routes"][0]["geometry"]["coordinates"]
            folium_coords = [(c[1], c[0]) for c in coords]
            folium.PolyLine(
                locations=folium_coords,
                color="blue",
                weight=4,
                opacity=0.8
            ).add_to(m)
        else:
            print("OSRM error code:", data.get("code"))
    except requests.exceptions.RequestException as e:
        print("OSRM request exception:", e)

##########################
# 3) Main View: Add/clear fires, nearest station, 3 hydrants, severity
##########################

def fires_map_view(request):
    """
    Allows user to:
      - Add one random fire (GET ?action=add)
      - Clear all fires (GET ?action=clear)
    Then draws them on Folium with:
      - 3 hydrants
      - nearest station
      - OSRM route station->each hydrant in blue
      - Fire severity predicted by an ML model => color of fire marker
        (green=low, orange=medium, red=high)
    """
    # parse ?action
    action = request.GET.get('action')
    fires = request.session.get('fires', [])

    if action == 'clear':
        fires = []
    elif action == 'add':
        # bounding box near Rosemont
        MIN_LAT, MAX_LAT = 45.53, 45.58
        MIN_LON, MAX_LON = -73.62, -73.55
        f_lat = random.uniform(MIN_LAT, MAX_LAT)
        f_lon = random.uniform(MIN_LON, MAX_LON)
        fires.append({"lat": f_lat, "lon": f_lon})

    request.session['fires'] = fires

    # read CSV
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")
    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # create folium map
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

    for idx, f in enumerate(fires, start=1):
        f_lat, f_lon = f["lat"], f["lon"]

        # 1) find nearest station
        best_station = None
        best_dist = float("inf")
        for s in stations:
            d_s = haversine_distance(f_lat, f_lon, s["lat"], s["lon"])
            if d_s < best_dist:
                best_station = s
                best_dist = d_s

        # 2) find 3 nearest hydrants
        hyd_dist = []
        for h in hydrants:
            d_h = haversine_distance(f_lat, f_lon, h["lat"], h["lon"])
            hyd_dist.append({**h, "dist": d_h})
        hyd_dist.sort(key=lambda x: x["dist"])
        top3_hydrants = hyd_dist[:3]

        # 3) compute dist_station feature & pick a random time_of_day
        dist_station = best_dist
        from datetime import datetime
        now_hour = datetime.now().hour  # example "time_of_day"

        # 4) Predict severity => color marker
        # Our model expects [lat, lon, dist_station, time_of_day]
        # exactly as we used in training
        severity = severity_model.predict([[f_lat, f_lon, dist_station, now_hour]])[0]

        color_map = {
            "low": "green",
            "medium": "orange",
            "high": "red"
        }
        fire_color = color_map.get(severity, "red")

        # 5) Mark the fire
        folium.Marker(
            [f_lat, f_lon],
            icon=folium.Icon(color=fire_color, icon="fire"),
            popup=f"Fire #{idx} (severity={severity})"
        ).add_to(m)

        # 6) Mark station in green
        if best_station:
            folium.Marker(
                [best_station["lat"], best_station["lon"]],
                icon=folium.Icon(color='green', icon='home'),
                popup=f"Station for Fire #{idx}"
            ).add_to(m)

        # 7) Mark 3 hydrants in blue & OSRM route from station->hydrant in blue
        for h_i, hyd in enumerate(top3_hydrants, start=1):
            folium.Marker(
                [hyd["lat"], hyd["lon"]],
                icon=folium.Icon(color='blue', icon='tint'),
                popup=f"Fire #{idx} Hydrant {h_i}"
            ).add_to(m)

            if best_station:
                add_osrm_route(m, best_station, hyd)

    # finalize
    map_html = m._repr_html_()
    return render(request, 'fires_map.html', {"map_html": map_html})