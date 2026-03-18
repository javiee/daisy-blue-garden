import logging
from datetime import date, timedelta
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def check_and_send_notifications():
    """
    Check for upcoming events and send Telegram notifications.
    Skips events that already have an unacknowledged notification,
    or that have been acknowledged and next_occurrence_date is in the future.
    """
    from .models import NotificationConfig, Notification
    from apps.events.models import CalendarEvent

    configs = NotificationConfig.objects.filter(is_active=True)
    sent_count = 0

    for config in configs:
        target_date = date.today() + timedelta(days=config.days_before)
        upcoming_events = CalendarEvent.objects.filter(
            date__lte=target_date,
            date__gte=date.today(),
        )

        for event in upcoming_events:
            # Skip if unacknowledged notification already exists
            if Notification.objects.filter(event=event, config=config, acknowledged=False).exists():
                continue

            # Skip if acknowledged but next_occurrence_date is in the future
            if Notification.objects.filter(
                event=event,
                config=config,
                acknowledged=True,
                next_occurrence_date__gt=date.today(),
            ).exists():
                continue

            send_event_notification.delay(event.pk, config.pk)
            sent_count += 1

    logger.info(f"Scheduled {sent_count} notifications")
    return sent_count


@shared_task
def send_event_notification(event_id: int, config_id: int):
    """Send notification for a specific event to a config's Telegram chat."""
    from .models import NotificationConfig, Notification
    from .bot import format_notification_message, send_notification_sync
    from apps.events.models import CalendarEvent

    try:
        event = CalendarEvent.objects.select_related('item').get(pk=event_id)
        config = NotificationConfig.objects.get(pk=config_id)
    except Exception as e:
        logger.error(f"Failed to load event/config: {e}")
        return None

    notification = Notification.objects.create(
        event=event,
        config=config,
        status='pending',
    )

    message = format_notification_message(event, notification)
    message_id = send_notification_sync(config.telegram_chat_id, message)

    if message_id:
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.telegram_message_id = message_id
    else:
        notification.status = 'failed'

    notification.save()
    return notification.pk
