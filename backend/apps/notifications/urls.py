from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationConfigViewSet

router = DefaultRouter()
router.register(r'config', NotificationConfigViewSet, basename='notification-config')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
