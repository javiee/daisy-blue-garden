from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationConfig
from .serializers import NotificationSerializer, NotificationConfigSerializer


class NotificationConfigViewSet(viewsets.ModelViewSet):
    queryset = NotificationConfig.objects.all()
    serializer_class = NotificationConfigSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.select_related('event', 'event__item').all()
    serializer_class = NotificationSerializer

    @action(detail=False, methods=['get'])
    def pending(self, request):
        pending = self.get_queryset().filter(acknowledged=False, status='sent')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        notification = self.get_object()
        if notification.acknowledged:
            return Response(
                {'detail': 'Already acknowledged.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        notification.acknowledge()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
