from unittest.mock import patch, MagicMock
from django.test import TestCase
from datetime import date, timedelta
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.notifications.models import NotificationConfig, Notification


class CheckAndSendNotificationsTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.config = NotificationConfig.objects.create(
            telegram_chat_id='12345', frequency='weekly', days_before=3
        )
        self.event = CalendarEvent.objects.create(
            item=self.item,
            title='Water Rose',
            date=date.today() + timedelta(days=2),
            recurrence='weekly',
            event_type='watering',
        )

    @patch('apps.notifications.tasks.send_event_notification')
    def test_sends_notification_for_upcoming_event(self, mock_send):
        mock_send.delay = MagicMock()
        from apps.notifications.tasks import check_and_send_notifications
        count = check_and_send_notifications()
        self.assertEqual(count, 1)
        mock_send.delay.assert_called_once_with(self.event.pk, self.config.pk)

    @patch('apps.notifications.tasks.send_event_notification')
    def test_skips_already_notified_unacknowledged(self, mock_send):
        mock_send.delay = MagicMock()
        Notification.objects.create(event=self.event, config=self.config, status='sent')
        from apps.notifications.tasks import check_and_send_notifications
        count = check_and_send_notifications()
        self.assertEqual(count, 0)

    @patch('apps.notifications.tasks.send_event_notification')
    def test_skips_acknowledged_with_future_occurrence(self, mock_send):
        mock_send.delay = MagicMock()
        notif = Notification.objects.create(event=self.event, config=self.config, status='sent')
        notif.acknowledged = True
        notif.next_occurrence_date = date.today() + timedelta(days=7)
        notif.save()
        from apps.notifications.tasks import check_and_send_notifications
        count = check_and_send_notifications()
        self.assertEqual(count, 0)


class SendEventNotificationTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.config = NotificationConfig.objects.create(telegram_chat_id='12345')
        self.event = CalendarEvent.objects.create(
            item=self.item,
            title='Water Rose',
            date=date.today() + timedelta(days=2),
            recurrence='weekly',
            event_type='watering',
        )

    @patch('apps.notifications.tasks.send_notification_sync')
    def test_creates_sent_notification(self, mock_send):
        mock_send.return_value = '999'
        from apps.notifications.tasks import send_event_notification
        notif_id = send_event_notification(self.event.pk, self.config.pk)
        notif = Notification.objects.get(pk=notif_id)
        self.assertEqual(notif.status, 'sent')
        self.assertEqual(notif.telegram_message_id, '999')

    @patch('apps.notifications.tasks.send_notification_sync')
    def test_marks_failed_when_send_fails(self, mock_send):
        mock_send.return_value = None
        from apps.notifications.tasks import send_event_notification
        notif_id = send_event_notification(self.event.pk, self.config.pk)
        notif = Notification.objects.get(pk=notif_id)
        self.assertEqual(notif.status, 'failed')
