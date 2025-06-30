from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('traceability.urls', namespace='traceability')),
    path('accounts/', include('allauth.urls')),
    path('api/', include('traceability.api.urls', namespace='api')),
]