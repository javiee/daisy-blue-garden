from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationConfig
from .serializers import NotificationSerializer, NotificationConfigSerializer
from .bot import send_notification_sync


class NotificationConfigViewSet(viewsets.ModelViewSet):
    queryset = NotificationConfig.objects.all()
    serializer_class = NotificationConfigSerializer

    @action(detail=True, methods=['post'], url_path='test')
    def test_notification(self, request, pk=None):
        config = self.get_object()
        message = (
            "🌸 *DaisyBlue Test Notification*\n\n"
            "Your Telegram connection is working correctly.\n"
            f"Chat ID: `{config.telegram_chat_id}`"
        )
        message_id = send_notification_sync(config.telegram_chat_id, message)
        if message_id:
            return Response({'status': 'sent', 'message_id': message_id})
        return Response(
            {'status': 'failed', 'detail': 'Could not send message. Check TELEGRAM_BOT_TOKEN and chat ID.'},
            status=status.HTTP_400_BAD_REQUEST,
        )



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
