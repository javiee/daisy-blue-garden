from datetime import date
from unittest import mock
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import TestCase
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.events import scheduler
from apps.events.scheduler import generate_recurring_events


class GeneralTaskAPITest(APITestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.plant_event = CalendarEvent.objects.create(
            item=self.item, title='Water Rose', date=date.today(),
            recurrence='once', event_type='watering',
        )

    def test_create_event_without_item(self):
        data = {
            'title': 'Clean gutters',
            'date': '2026-10-20',
            'recurrence': 'once',
            'event_type': 'other',
        }
        response = self.client.post('/api/v1/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = CalendarEvent.objects.get(pk=response.data['id'])
        self.assertIsNone(event.item)

    def test_general_filter_returns_only_itemless_events(self):
        task = CalendarEvent.objects.create(
            title='Mow lawn', date=date.today(),
            recurrence='weekly', event_type='other',
        )
        response = self.client.get('/api/v1/events/?general=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [e['id'] for e in response.data['results']]
        self.assertIn(task.pk, ids)
        self.assertNotIn(self.plant_event.pk, ids)

    def test_general_filter_combines_with_base_only(self):
        base = CalendarEvent.objects.create(
            title='Mow lawn', date=date(2026, 2, 1),
            recurrence='monthly', event_type='other',
            end_date=date(2026, 6, 30), repeats_yearly=True,
        )
        generate_recurring_events(base)
        self.assertTrue(CalendarEvent.objects.filter(parent_event=base).exists())

        response = self.client.get('/api/v1/events/?general=true&base_only=true')
        ids = [e['id'] for e in response.data['results']]
        self.assertIn(base.pk, ids)
        self.assertNotIn(
            [o.pk for o in base.occurrences.all()], ids
        )


class FrozenDate(date):
    """date with a frozen today() so the 6-month cap is deterministic."""

    @classmethod
    def today(cls):
        return cls(2026, 10, 7)


class GeneralTaskSchedulerTest(TestCase):
    def test_expands_recurring_task_without_item(self):
        base = CalendarEvent.objects.create(
            title='Mow lawn', date=date(2026, 10, 10),
            recurrence='weekly', event_type='other',
        )
        with mock.patch.object(scheduler, 'date', FrozenDate):
            generate_recurring_events(base, months_ahead=6)
        occurrences = list(base.occurrences.all())
        self.assertGreater(len(occurrences), 0)
        self.assertTrue(all(o.item is None for o in occurrences))

    def test_task_occurrences_are_idempotent(self):
        base = CalendarEvent.objects.create(
            title='Mow lawn', date=date(2026, 10, 10),
            recurrence='weekly', event_type='other',
        )
        with mock.patch.object(scheduler, 'date', FrozenDate):
            generate_recurring_events(base, months_ahead=6)
            first = base.occurrences.count()
            generate_recurring_events(base, months_ahead=6)
            second = base.occurrences.count()
        self.assertEqual(first, second)
