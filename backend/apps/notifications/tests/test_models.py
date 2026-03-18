from django.test import TestCase
from datetime import date, timedelta
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.notifications.models import NotificationConfig, Notification


class NotificationConfigTest(TestCase):
    def test_create_config(self):
        config = NotificationConfig.objects.create(
            telegram_chat_id='12345', frequency='weekly', days_before=3,
        )
        self.assertEqual(str(config), 'Config for chat 12345 (weekly)')

    def test_default_frequency_weekly(self):
        config = NotificationConfig.objects.create(telegram_chat_id='99999')
        self.assertEqual(config.frequency, 'weekly')
        self.assertEqual(config.days_before, 3)
        self.assertTrue(config.is_active)


class NotificationAcknowledgeTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.config = NotificationConfig.objects.create(telegram_chat_id='12345')

    def _make_notification(self, recurrence):
        event = CalendarEvent.objects.create(
            item=self.item,
            title='Test',
            date=date.today() + timedelta(days=2),
            recurrence=recurrence,
            event_type='watering',
        )
        return Notification.objects.create(event=event, config=self.config, status='sent')

    def test_acknowledge_sets_fields(self):
        notif = self._make_notification('weekly')
        notif.acknowledge()
        self.assertTrue(notif.acknowledged)
        self.assertIsNotNone(notif.acknowledged_at)

    def test_weekly_next_occurrence(self):
        notif = self._make_notification('weekly')
        notif.acknowledge()
        self.assertEqual(notif.next_occurrence_date, date.today() + timedelta(weeks=1))

    def test_monthly_next_occurrence(self):
        notif = self._make_notification('monthly')
        notif.acknowledge()
        today = date.today()
        month = today.month + 1
        year = today.year
        if month > 12:
            month, year = 1, year + 1
        expected = today.replace(year=year, month=month)
        self.assertEqual(notif.next_occurrence_date, expected)

    def test_once_next_occurrence_is_none(self):
        notif = self._make_notification('once')
        notif.acknowledge()
        self.assertIsNone(notif.next_occurrence_date)

    def test_yearly_next_occurrence(self):
        notif = self._make_notification('yearly')
        notif.acknowledge()
        expected = date.today().replace(year=date.today().year + 1)
        self.assertEqual(notif.next_occurrence_date, expected)
