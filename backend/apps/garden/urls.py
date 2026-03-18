from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GardenItemViewSet

router = DefaultRouter()
router.register(r'', GardenItemViewSet, basename='garden-item')

urlpatterns = [
    path('', include(router.urls)),
]
