import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent


class GenerateItemCareAsyncTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')

    @patch('apps.llm.tasks.GardenLLMService')
    def test_creates_events_from_llm(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.generate_item_description.return_value = {
            'description': 'A red rose',
            'cares': 'Water weekly',
        }
        mock_service.generate_care_schedule.return_value = [
            {
                'title': 'Water Rose',
                'description': 'Water at base',
                'event_type': 'watering',
                'recurrence': 'weekly',
                'days_from_now': 1,
            }
        ]

        from apps.llm.tasks import generate_item_care_async
        count = generate_item_care_async(self.item.pk)

        self.assertEqual(count, 1)
        self.assertEqual(CalendarEvent.objects.count(), 1)
        event = CalendarEvent.objects.first()
        self.assertEqual(event.event_type, 'watering')
        self.assertEqual(event.item, self.item)

    @patch('apps.llm.tasks.GardenLLMService')
    def test_updates_item_description(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.generate_item_description.return_value = {
            'description': 'Updated description',
            'cares': 'Updated cares',
        }
        mock_service.generate_care_schedule.return_value = []

        from apps.llm.tasks import generate_item_care_async
        generate_item_care_async(self.item.pk)

        self.item.refresh_from_db()
        self.assertEqual(self.item.description, 'Updated description')
        self.assertEqual(self.item.cares, 'Updated cares')

    def test_handles_nonexistent_item(self):
        from apps.llm.tasks import generate_item_care_async
        result = generate_item_care_async(99999)
        self.assertIsNone(result)
