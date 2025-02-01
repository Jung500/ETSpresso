# this_is_fine/views.py
import folium
from django.shortcuts import render

def map_view(request):
    # Create a map centered around a specific location (latitude, longitude)
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
    
    # Add a marker to the map (optional)
    folium.Marker([40.7128, -74.0060], popup='New York City').add_to(m)
    
    # Save map as an HTML string
    map_html = m._repr_html_()  # This generates the HTML representation of the map
    
    # Pass the map HTML to the template
    return render(request, 'map.html', {'map_html': map_html})
