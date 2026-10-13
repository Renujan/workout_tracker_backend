"""
ProgressX API root URL configuration.
All API endpoints are versioned under /api/v1/.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from .views import HealthCheckView, UserDataArchiveExportView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check & system export
    path('api/v1/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/v1/export/userdata/', UserDataArchiveExportView.as_view(), name='core-user-data-export'),

    # JWT token endpoints
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App routers
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/users/', include('users.urls_profile')),
    path('api/v1/exercises/', include('exercises.urls')),
    path('api/v1/workouts/', include('workouts.urls')),
    path('api/v1/nutrition/', include('nutrition.urls')),
    path('api/v1/progress/', include('progress.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
