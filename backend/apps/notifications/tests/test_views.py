from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.notifications.models import NotificationConfig, Notification


class NotificationConfigAPITest(APITestCase):
    def test_create_config(self):
        data = {'telegram_chat_id': '12345', 'frequency': 'weekly', 'days_before': 3}
        response = self.client.post('/api/v1/notifications/config/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_configs(self):
        NotificationConfig.objects.create(telegram_chat_id='12345')
        response = self.client.get('/api/v1/notifications/config/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class NotificationAPITest(APITestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')
        self.config = NotificationConfig.objects.create(telegram_chat_id='12345')
        self.event = CalendarEvent.objects.create(
            item=self.item, title='Water Rose',
            date=date.today() + timedelta(days=2),
            recurrence='weekly', event_type='watering',
        )
        self.notification = Notification.objects.create(
            event=self.event, config=self.config, status='sent'
        )

    def test_list_notifications(self):
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_notifications(self):
        response = self.client.get('/api/v1/notifications/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_acknowledge(self):
        response = self.client.post(
            f'/api/v1/notifications/{self.notification.pk}/acknowledge/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.acknowledged)

    def test_acknowledge_twice_returns_400(self):
        self.notification.acknowledge()
        response = self.client.post(
            f'/api/v1/notifications/{self.notification.pk}/acknowledge/'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
