from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.events.scheduler import generate_recurring_events


class CalendarEventAPITest(APITestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.event = CalendarEvent.objects.create(
            item=self.item,
            title='Water Rose',
            date=date.today(),
            recurrence='weekly',
            event_type='watering',
        )

    def _occurrence_dates(self, base):
        return set(CalendarEvent.objects.filter(parent_event=base).values_list('date', flat=True))

    def _create_expanded_base(self, title='Fertilize Rose'):
        base = CalendarEvent.objects.create(
            item=self.item, title=title, date=date(2026, 2, 15),
            recurrence='monthly', event_type='fertilizing',
            end_date=date(2026, 6, 30), repeats_yearly=True,
        )
        generate_recurring_events(base)
        return base

    def test_list_events(self):
        response = self.client.get('/api/v1/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_event(self):
        data = {
            'item': self.item.pk,
            'title': 'Fertilize Rose',
            'date': str(date.today()),
            'recurrence': 'monthly',
            'event_type': 'fertilizing',
        }
        response = self.client.post('/api/v1/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_filter_by_month(self):
        month_str = date.today().strftime('%Y-%m')
        response = self.client.get(f'/api/v1/events/?month={month_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_week(self):
        iso = date.today().isocalendar()
        week_str = f'{iso.year}-W{iso.week:02d}'
        response = self.client.get(f'/api/v1/events/?week={week_str}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_events_by_item(self):
        response = self.client.get(f'/api/v1/events/by-item/{self.item.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_event(self):
        response = self.client.delete(f'/api/v1/events/{self.event.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_event_saves_repeats_yearly(self):
        data = {
            'item': self.item.pk,
            'title': 'Fertilize Rose',
            'date': '2026-02-15',
            'recurrence': 'monthly',
            'event_type': 'fertilizing',
            'end_date': '2026-06-30',
            'repeats_yearly': False,
        }
        response = self.client.post('/api/v1/events/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = CalendarEvent.objects.get(pk=response.data['id'])
        self.assertFalse(event.repeats_yearly)

    def test_update_base_event_reexpands_series(self):
        base = self._create_expanded_base()
        self.assertIn(date(2026, 3, 15), self._occurrence_dates(base))

        response = self.client.patch(
            f'/api/v1/events/{base.pk}/', {'date': '2026-03-01'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dates = self._occurrence_dates(base)
        self.assertIn(date(2026, 4, 1), dates)      # new series from 2026-03-01
        self.assertNotIn(date(2026, 3, 15), dates)  # stale series is gone
        self.assertNotIn(date(2026, 4, 15), dates)  # no orphans left behind

    def test_update_occurrence_only_edits_that_row(self):
        base = self._create_expanded_base()
        occurrence = CalendarEvent.objects.filter(parent_event=base).first()

        response = self.client.patch(
            f'/api/v1/events/{occurrence.pk}/', {'date': '2026-12-01'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        occurrence.refresh_from_db()
        self.assertEqual(occurrence.date, date(2026, 12, 1))
        # the rest of the series is untouched
        self.assertIn(date(2026, 4, 15), self._occurrence_dates(base))

    def test_delete_base_event_removes_occurrences(self):
        base = self._create_expanded_base()
        self.assertTrue(CalendarEvent.objects.filter(parent_event=base).exists())

        response = self.client.delete(f'/api/v1/events/{base.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # only the setUp event remains (occurrences must not be orphaned)
        self.assertEqual(CalendarEvent.objects.filter(item=self.item).count(), 1)
