# this_is_fine/urls.py

from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.fires_map_view, name='fires_map_view'),
]