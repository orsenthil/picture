"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from pictures.views import picture_of_the_day_view, privacy_policy_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pictures.urls')),  # Unified API
    path('favicon.ico', RedirectView.as_view(url='/static/pictures/favicon.ico', permanent=True)),
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('', picture_of_the_day_view, name='picture_of_the_day'),  # Root route
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

