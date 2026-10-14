from datetime import date
from django.test import TestCase
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.notifications.models import Notification
from apps.notifications.bot import format_notification_message


class FormatNotificationMessageTest(TestCase):
    def test_message_includes_plant_when_event_has_one(self):
        item = GardenItem.objects.create(name='Rose', type='plant')
        event = CalendarEvent.objects.create(
            item=item, title='Water Rose', date=date(2026, 10, 10),
            recurrence='weekly', event_type='watering',
        )
        notification = Notification.objects.create(event=event, status='pending')
        message = format_notification_message(event, notification)
        self.assertIn('Rose', message)
        self.assertIn('/ack', message)

    def test_message_for_task_without_item_omits_plant_line(self):
        event = CalendarEvent.objects.create(
            title='Mow lawn', date=date(2026, 10, 10),
            recurrence='weekly', event_type='other',
        )
        notification = Notification.objects.create(event=event, status='pending')
        message = format_notification_message(event, notification)
        self.assertIn('Mow lawn', message)
        self.assertNotIn('Plant:', message)
        self.assertIn('/ack', message)

    def test_ack_command_underscore_is_markdown_safe(self):
        # A bare underscore in legacy Telegram Markdown opens an unclosed
        # italic entity and makes Telegram reject the whole message.
        event = CalendarEvent.objects.create(
            title='Mow lawn', date=date(2026, 10, 10),
            recurrence='weekly', event_type='other',
        )
        notification = Notification.objects.create(event=event, status='pending')
        message = format_notification_message(event, notification)
        self.assertNotIn(f'/ack_{notification.pk}', message)
        self.assertIn(f'/ack\\_{notification.pk}', message)

    def test_markdown_chars_in_title_and_description_are_escaped(self):
        event = CalendarEvent.objects.create(
            title='Fix *gate* and _fence_',
            description='Use 5*3 boards',
            date=date(2026, 10, 10),
            recurrence='once', event_type='other',
        )
        notification = Notification.objects.create(event=event, status='pending')
        message = format_notification_message(event, notification)
        self.assertIn('Fix \\*gate\\* and \\_fence\\_', message)
        self.assertIn('Use 5\\*3 boards', message)
