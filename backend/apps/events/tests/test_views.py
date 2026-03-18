from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent


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
