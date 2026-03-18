from django.test import TestCase
from datetime import date
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent


class CalendarEventModelTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')

    def test_create_event(self):
        event = CalendarEvent.objects.create(
            item=self.item,
            title='Water Rose',
            date=date.today(),
            recurrence='weekly',
            event_type='watering',
        )
        self.assertEqual(str(event), f'Water Rose - {date.today()}')

    def test_event_linked_to_item(self):
        event = CalendarEvent.objects.create(
            item=self.item,
            title='Prune Rose',
            date=date.today(),
            recurrence='once',
            event_type='pruning',
        )
        self.assertIn(event, self.item.events.all())

    def test_ordering_by_date(self):
        e1 = CalendarEvent.objects.create(
            item=self.item, title='E1', date=date(2024, 3, 1), recurrence='once', event_type='other'
        )
        e2 = CalendarEvent.objects.create(
            item=self.item, title='E2', date=date(2024, 1, 1), recurrence='once', event_type='other'
        )
        events = list(CalendarEvent.objects.all())
        self.assertEqual(events[0], e2)
        self.assertEqual(events[1], e1)
