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
# 2) Utility Functions
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
           f"{s_lon},{s_lat};{h_lon},{h_lat}"
           f"?overview=full&geometries=geojson")

    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("code") == "Ok":
            coords = data["routes"][0]["geometry"]["coordinates"]  # [ [lon, lat], ... ]
            folium_coords = [(c[1], c[0]) for c in coords]          # [ (lat, lon), ... ]
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
    - Session-based list of fires
    - ?action=add => add random bounding-box fire
    - ?action=clear => remove all
    - ?action=place&lat=..&lon=.. => user click on map to place fire
    - ?manual=1 => manual mode on => clicking map places fires
    For each fire:
      - We find the single NEAREST station
      - We pick 3 hydrants
      - We do OSRM station->hydrant routes in BLUE
      - We run ML severity => color the fire (green/orange/red)
    """

    fires = request.session.get('fires', [])
    action = request.GET.get('action')
    manual = request.GET.get('manual','0')

    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')

    if action == 'clear':
        fires = []
    elif action == 'add':
        # random bounding box near Rosemont
        MIN_LAT, MAX_LAT = 45.53, 45.58
        MIN_LON, MAX_LON = -73.62, -73.55
        lat = random.uniform(MIN_LAT, MAX_LAT)
        lon = random.uniform(MIN_LON, MAX_LON)
        fires.append({"lat": lat, "lon": lon})
    elif action == 'place' and lat_str and lon_str:
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            fires.append({"lat": lat, "lon": lon})
        except ValueError:
            pass

    request.session['fires'] = fires

    # load data
    hydrants_csv = os.path.join(settings.BASE_DIR, "resources/aqu_borneincendie_p.csv")
    stations_csv = os.path.join(settings.BASE_DIR, "resources/casernes.csv")

    hydrants = read_hydrants(hydrants_csv)
    stations = read_stations(stations_csv)

    # create Folium map
    m = folium.Map(location=[45.55, -73.58], zoom_start=13)

    # For each fire, find 1 station, 3 hydrants, do OSRM, etc.
    for idx, fire in enumerate(fires, start=1):
        f_lat, f_lon = fire["lat"], fire["lon"]

        # nearest station
        best_station = None
        best_dist = float("inf")
        for st in stations:
            dist_st = haversine_distance(f_lat, f_lon, st["lat"], st["lon"])
            if dist_st < best_dist:
                best_dist = dist_st
                best_station = st

        # 3 hydrants
        hydr_with_dist = []
        for hy in hydrants:
            d_hy = haversine_distance(f_lat, f_lon, hy["lat"], hy["lon"])
            hydr_with_dist.append({**hy, "dist": d_hy})
        hydr_with_dist.sort(key=lambda x: x["dist"])
        top3 = hydr_with_dist[:3]

        # ML severity => color
        now_hour = datetime.now().hour
        station_dist = best_dist if best_station else 0
        severity = severity_model.predict([[f_lat, f_lon, station_dist, now_hour]])[0]

        color_map = {"low":"green","medium":"orange","high":"red"}
        fire_color = color_map.get(severity, "red")

        # Mark the fire
        folium.Marker(
            [f_lat, f_lon],
            icon=folium.Icon(color=fire_color, icon="fire"),
            popup=f"Fire #{idx}, severity={severity}"
        ).add_to(m)

        # Mark station in green
        if best_station:
            folium.Marker(
                [best_station["lat"], best_station["lon"]],
                icon=folium.Icon(color='green', icon='home'),
                popup=f"Fire #{idx} Station"
            ).add_to(m)

        # Mark hydrants in blue + route from station->hydrant
        if best_station:
            for h_i, h in enumerate(top3, start=1):
                folium.Marker(
                    [h["lat"], h["lon"]],
                    icon=folium.Icon(color='blue', icon='tint'),
                    popup=f"Fire #{idx} Hydrant {h_i}"
                ).add_to(m)
                add_osrm_route(m, best_station, h)

    # produce map HTML
    map_name = m.get_name()
    map_html = m._repr_html_()

    # if manual=1 => extra JS to place fires by map click
    extra_js = ""
    if manual == '1':
        extra_js = f"""
        <script>
        document.addEventListener("DOMContentLoaded", function() {{
          let mapVar = window["{map_name}"];
          if (!mapVar) {{
            console.log("Can't find folium map object {map_name}");
            return;
          }}
          console.log("Manual mode ON => click to place fires");
          mapVar.on('click', function(e) {{
            let lat = e.latlng.lat;
            let lon = e.latlng.lng;
            window.location.href = '?action=place&lat=' + lat + '&lon=' + lon + '&manual=1';
          }});
        }});
        </script>
        """

    return render(request, 'fires_map.html', {
        "map_html": map_html,
        "manual": manual,
        "extra_js": extra_js,
    })