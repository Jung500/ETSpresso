import random
import folium

def define_montreal_square():
    """
    Defines a square (as a list of (lat, lon) tuples) around downtown Montreal.
    """
    center_lat = 45.5017
    center_lon = -73.5673
    half_side = 0.025  # approx 2.5km in lat/lon terms

    # bottom-left, bottom-right, top-right, top-left
    square_coords = [
        (center_lat - half_side, center_lon - half_side),
        (center_lat - half_side, center_lon + half_side),
        (center_lat + half_side, center_lon + half_side),
        (center_lat + half_side, center_lon - half_side),
    ]
    return square_coords

def generate_random_points_in_square(square, n=5):
    """
    Generates n random (lat, lon) points inside the bounding square.
    """
    lats = [pt[0] for pt in square]
    lons = [pt[1] for pt in square]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    points = []
    for _ in range(n):
        rand_lat = random.uniform(min_lat, max_lat)
        rand_lon = random.uniform(min_lon, max_lon)
        points.append((rand_lat, rand_lon))
    return points

def create_map_with_random_points(n=5, map_filename="montreal_random_points.html"):
    """
    Creates a Folium map showing a bounding box + n random points inside it.
    """
    square = define_montreal_square()
    random_pts = generate_random_points_in_square(square, n)

    # Center around downtown Montreal
    m = folium.Map(location=[45.5017, -73.5673], zoom_start=14)

    # Draw the bounding box
    folium.PolyLine(
        locations=square + [square[0]],  # repeat the first point to close
        color='green',
        weight=2,
        opacity=0.8
    ).add_to(m)

    # Add each random point
    for pt in random_pts:
        folium.Marker(
            location=pt,
            icon=folium.Icon(color='red'),
            popup=f"Random Point: {pt}"
        ).add_to(m)

    m.save(map_filename)
    print(f"Map saved as {map_filename}")

# If run directly, it generates 5 random points and saves montreal_random_points.html
if __name__ == '__main__':
    create_map_with_random_points(n=5)