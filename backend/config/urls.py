from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/geoglows/', include('global_waterlevel_forecast.urls')),
]
