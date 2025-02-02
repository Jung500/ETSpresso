# this_is_fine/views.py

import os
import math
import random
import csv
import requests
import joblib
from datetime import datetime

from django.conf import settings
from django.shortcuts import render
import folium

###################################
# 1) Load the ML model once
###################################
MODEL_PATH = os.path.join(settings.BASE_DIR, "severity_model.pkl")
severity_model = joblib.load(MODEL_PATH)

###################################
# 2) CSV Reading & Helpers
###################################

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
        print("Hydrants CSV not found at", csv_path)
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
        print("Stations CSV not found at", csv_path)
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
    Station->Hydrant route in BLUE, using OSRM.
    """
    s_lat, s_lon = station["lat"], station["lon"]
    h_lat, h_lon = hydrant["lat"], hydrant["lon"]

    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{s_lon},{s_lat};{h_lon},{h_lat}?"
           f"overview=full&geometries=geojson")

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("code") == "Ok":
            coords = data["routes"][0]["geometry"]["coordinates"]  # [ [lon,lat], ... ]
            folium_coords = [(c[1], c[0]) for c in coords]          # [ (lat,lon), ... ]
            folium.PolyLine(
                locations=folium_coords,
                color="blue",
                weight=4,
                opacity=0.8
            ).add_to(m)
        else:
            print("OSRM route error:", data.get("code"))
    except requests.exceptions.RequestException as e:
        print("OSRM request error:", e)


###################################
# 3) The Main View
###################################

def fires_map_view(request):
    """
    Lets user:
     - Add random fires (Add Fire)
     - Clear all fires
     - Toggle "Manual" mode => click map to place a fire
    Only 1 station per 2 fires, 3 hydrants each, OSRM routes in blue, ML severity coloring.
    """
    # session-based list of fires
    fires = request.session.get('fires', [])

    # parse query
    action = request.GET.get('action')   # add, clear, place
    manual = request.GET.get('manual','0')  # '1' or '0'
    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')

    if action == 'clear':
        fires = []
    elif action == 'add':
        # random bounding box near Rosemont
        MIN_LAT, MAX_LAT = 45.53, 45.58
        MIN_LON, MAX_LON = -73.62, -73.55
        f_lat = random.uniform(MIN_LAT, MAX_LAT)
        f_lon = random.uniform(MIN_LON, MAX_LON)
        fires.append({"lat": f_lat, "lon": f_lon})
    elif action == 'place':
        # user manually clicks => lat/lon from GET
        if lat_str and lon_str:
            try:
                f_lat = float(lat_str)
                f_lon = float(lon_str)
                fires.append({"lat": f_lat, "lon": f_lon})
            except ValueError:
                pass

    request.session['fires'] = fires

    # read CSV
    hydrants_csv = os.path.join(settings.BASE_DIR, "aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "casernes.csv")
    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # create Folium map
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

    # group fires in pairs => 1 station per 2 fires
    pair_of_fires = []
    for i in range(0, len(fires), 2):
        chunk = fires[i:i+2]
        pair_of_fires.append(chunk)

    # process each chunk
    chunk_idx = 0
    for chunk in pair_of_fires:
        chunk_idx += 1
        # pick station based on the first fire in chunk
        if not chunk:
            continue
        first_fire = chunk[0]

        # find nearest station
        best_station = None
        best_dist = float('inf')
        for st in stations:
            dist_st = haversine_distance(first_fire["lat"], first_fire["lon"], st["lat"], st["lon"])
            if dist_st < best_dist:
                best_dist = dist_st
                best_station = st

        # for each fire in chunk
        for idx_in_chunk, single_fire in enumerate(chunk, start=1):
            # find 3 hydrants
            hydr_dist = []
            for h in hydrants:
                d_h = haversine_distance(single_fire["lat"], single_fire["lon"], h["lat"], h["lon"])
                hydr_dist.append({**h, "dist": d_h})
            hydr_dist.sort(key=lambda x: x["dist"])
            top3 = hydr_dist[:3]

            # predict severity => color
            now_hour = datetime.now().hour
            station_dist = haversine_distance(
                single_fire["lat"], single_fire["lon"],
                best_station["lat"], best_station["lon"]
            ) if best_station else 0
            severity = severity_model.predict([[single_fire["lat"], single_fire["lon"], station_dist, now_hour]])[0]
            color_map = {"low":"green","medium":"orange","high":"red"}
            fire_color = color_map.get(severity, "red")

            # place the fire marker
            folium.Marker(
                [single_fire["lat"], single_fire["lon"]],
                icon=folium.Icon(color=fire_color, icon='fire'),
                popup=f"Fire => severity={severity}"
            ).add_to(m)

            # place station marker for the chunk's first fire only
            if idx_in_chunk == 1 and best_station:
                folium.Marker(
                    [best_station["lat"], best_station["lon"]],
                    icon=folium.Icon(color='green', icon='home'),
                    popup=f"Station for chunk #{chunk_idx}"
                ).add_to(m)

            # place hydrants + OSRM route
            if best_station:
                for hyd_i, hyd in enumerate(top3, start=1):
                    folium.Marker(
                        [hyd["lat"], hyd["lon"]],
                        icon=folium.Icon(color='blue', icon='tint'),
                        popup=f"Hydrant {hyd_i}"
                    ).add_to(m)
                    add_osrm_route(m, best_station, hyd)

    # convert to HTML
    map_name = m.get_name()  # e.g. "map_f3b2d1067ab..."
    map_html = m._repr_html_()

    # If manual=1 => we add a JS snippet that references the real map object name
    extra_js = ""
    if manual == '1':
        extra_js = f"""
        <script>
        document.addEventListener("DOMContentLoaded", function() {{
          // The real Folium map object is window["{map_name}"]
          let mapVar = window["{map_name}"];
          if (!mapVar) {{
            console.log("Could not find folium map object named {map_name}");
            return;
          }}
          console.log("Manual mode ON => click map to place fires");
          mapVar.on('click', function(e) {{
            let lat = e.latlng.lat;
            let lon = e.latlng.lng;
            // request => ?action=place&lat=..&lon=..&manual=1
            window.location.href = '?action=place&lat=' + lat + '&lon=' + lon + '&manual=1';
          }});
        }});
        </script>
        """

    # pass everything to the template
    return render(request, 'fires_map.html', {
        "map_html": map_html,
        "manual": manual,
        "extra_js": extra_js,
    })