from django.contrib import admin
from django.urls import path
from . import views  # views.py in the same folder

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # The home page with the button to generate random fires:
    path('', views.index_view, name='index_view'),

    # The route that processes the logic & returns a Folium map
    path('random_fires/', views.random_fires_view, name='random_fires_view'),
]