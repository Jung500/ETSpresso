import random
import folium

def define_montreal_square():
    """
    Defines a square (as a list of four (lat, lon) tuples) inside the Montreal island.
    The square is centered on downtown Montreal (approx. 45.5017, -73.5673)
    with a half side length of 0.025°.
    """
    center_lat = 45.5017
    center_lon = -73.5673
    half_side = 0.025

    # Define square corners in order: bottom-left, bottom-right, top-right, top-left.
    square_coords = [
        (center_lat - half_side, center_lon - half_side),  # bottom-left
        (center_lat - half_side, center_lon + half_side),  # bottom-right
        (center_lat + half_side, center_lon + half_side),  # top-right
        (center_lat + half_side, center_lon - half_side),  # top-left
    ]
    return square_coords

def generate_random_points_in_square(square, n=5):
    """
    Generates n random points (lat, lon) inside an axis–aligned square.
    
    Parameters:
        square: a list of 4 tuples representing the square's corners.
        n: number of random points to generate.
    
    Returns:
        A list of (lat, lon) tuples.
    """
    # Get min and max latitude/longitude from the square's corners.
    lats = [pt[0] for pt in square]
    lons = [pt[1] for pt in square]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    random_points = []
    for _ in range(n):
        rand_lat = random.uniform(min_lat, max_lat)
        rand_lon = random.uniform(min_lon, max_lon)
        random_points.append((rand_lat, rand_lon))
    return random_points

def create_map_with_random_points(n=5, map_filename="montreal_random_points.html"):
    """
    Creates a folium map displaying the Montreal square and n random points within it.
    
    Parameters:
        n: Number of random points to generate.
        map_filename: Filename to save the map.
    """
    # Define the square and generate random points.
    square_coords = define_montreal_square()
    random_points = generate_random_points_in_square(square_coords, n)
    
    # Use the center of the square for the map's initial center.
    center = (45.5017, -73.5673)
    m = folium.Map(location=center, zoom_start=14)
    
    # Draw the square (close the polygon by adding the first point at the end).
    folium.PolyLine(
        locations=square_coords + [square_coords[0]],
        color='green',
        weight=2,
        opacity=0.8
    ).add_to(m)
    
    # Add markers for each random point.
    for pt in random_points:
        folium.Marker(
            location=pt,
            icon=folium.Icon(color='red'),
            popup=f"Random Point: {pt}"
        ).add_to(m)
    
    m.save(map_filename)
    print(f"Map saved as {map_filename}")

# When run directly, generate 5 random points and create the map.
if __name__ == '__main__':
    create_map_with_random_points(n=5)
