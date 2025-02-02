from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('map/', include('maps.urls')),  # ✅ Correctly include maps URLs
]