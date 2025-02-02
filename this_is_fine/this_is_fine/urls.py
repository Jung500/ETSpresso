# this_is_fine/this_is_fine/urls.py

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Add a path for your combined_map_view:
    path("combined-map/", views.combined_map_view, name="combined_map_view"),
]