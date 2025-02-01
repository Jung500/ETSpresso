# this_is_fine/views.py
import folium
from django.shortcuts import render

def map_view(request):
    # Create a map centered around Montreal (latitude, longitude)
    m = folium.Map(location=[45.5017, -73.5673], zoom_start=12)
    
    # Add a marker to the map (optional)
    folium.Marker([45.5017, -73.5673], popup='Montreal').add_to(m)
    
    # Save map as an HTML string
    map_html = m._repr_html_()  # This generates the HTML representation of the map
    
    # Pass the map HTML to the template
    return render(request, 'map.html', {'map_html': map_html})
