from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PictureOfTheDayViewSet

router = DefaultRouter()
router.register(r'pictures', PictureOfTheDayViewSet, basename='pictures')

urlpatterns = [
    path('', include(router.urls)),
]

