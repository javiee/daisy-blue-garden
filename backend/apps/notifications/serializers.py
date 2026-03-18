from rest_framework import serializers
from .models import Notification, NotificationConfig
from apps.events.serializers import CalendarEventSerializer


class NotificationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationConfig
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    event_detail = CalendarEventSerializer(source='event', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'sent_at', 'acknowledged_at',
            'next_occurrence_date', 'telegram_message_id', 'status',
        ]
