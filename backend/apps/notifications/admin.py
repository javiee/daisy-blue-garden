from django.contrib import admin
from .models import Notification, NotificationConfig


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ['telegram_chat_id', 'frequency', 'days_before', 'is_active']
    list_filter = ['frequency', 'is_active']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['event', 'status', 'sent_at', 'acknowledged', 'acknowledged_at']
    list_filter = ['status', 'acknowledged']
    search_fields = ['event__title']
    readonly_fields = ['sent_at', 'acknowledged_at', 'telegram_message_id']
    date_hierarchy = 'created_at'
