import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.llm.service import GardenLLMService


class GardenLLMServiceTest(TestCase):
    @patch('apps.llm.service.get_llm_provider')
    def test_generate_item_description_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'description': 'A beautiful rose',
            'cares': 'Water weekly, full sun',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.generate_item_description('Rose', 'plant')

        self.assertEqual(result['description'], 'A beautiful rose')
        self.assertEqual(result['cares'], 'Water weekly, full sun')

    @patch('apps.llm.service.get_llm_provider')
    def test_generate_item_description_handles_error(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception('API error')
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.generate_item_description('Rose', 'plant')

        self.assertEqual(result['description'], '')
        self.assertEqual(result['cares'], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_generate_care_schedule_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps([
            {
                'title': 'Water Rose',
                'description': 'Water at base',
                'event_type': 'watering',
                'recurrence': 'weekly',
                'days_from_now': 1,
            }
        ])
        mock_get_provider.return_value = mock_provider

        mock_item = MagicMock()
        mock_item.name = 'Rose'
        mock_item.type = 'plant'
        mock_item.description = 'A rose'
        mock_item.cares = 'Water weekly'

        service = GardenLLMService()
        events = service.generate_care_schedule(mock_item)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['event_type'], 'watering')

    @patch('apps.llm.service.get_llm_provider')
    def test_generate_care_schedule_handles_invalid_json(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = 'not valid json'
        mock_get_provider.return_value = mock_provider

        mock_item = MagicMock()
        mock_item.name = 'Rose'
        mock_item.type = 'plant'
        mock_item.description = ''
        mock_item.cares = ''

        service = GardenLLMService()
        events = service.generate_care_schedule(mock_item)
        self.assertEqual(events, [])
