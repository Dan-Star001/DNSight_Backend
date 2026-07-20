"""
URL configuration for DNSight_Backend project.

Routes all API endpoints through app-specific url modules using Django's
include() function. All app URLs are mounted under the /api/ prefix.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Each app owns its own URL namespace, all mounted under /api/
    path('api/', include('users.urls')),
    path('api/', include('hospitals.urls')),
    path('api/', include('patients.urls')),
    path('api/', include('assessments.urls')),
    path('api/', include('appointments.urls')),
    path('api/', include('analytics.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
