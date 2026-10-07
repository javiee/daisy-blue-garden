import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.core.models import AppSetting
from apps.llm.service import GardenLLMService, _strip_markdown_fences
from apps.llm.prompts import build_system_prompt


class BuildSystemPromptTest(TestCase):
    def test_english_instruction(self):
        self.assertIn('in English', build_system_prompt('en'))

    def test_spanish_instruction(self):
        self.assertIn('Spanish', build_system_prompt('es'))

    def test_unknown_language_falls_back_to_english(self):
        self.assertIn('in English', build_system_prompt('fr'))

    def test_default_persona_used_when_prompt_empty(self):
        from apps.llm.prompts import CARE_SYSTEM_PROMPT
        self.assertTrue(build_system_prompt('en', '').startswith(CARE_SYSTEM_PROMPT))
        self.assertTrue(
            build_system_prompt('en', '   \n  ').startswith(CARE_SYSTEM_PROMPT)
        )

    def test_custom_persona_replaces_default(self):
        custom = 'You are a gardener in Málaga, Mediterranean climate.'
        prompt = build_system_prompt('en', custom)
        self.assertTrue(prompt.startswith(custom))
        self.assertNotIn('professional botanist', prompt)

    def test_custom_persona_still_gets_language_instruction(self):
        prompt = build_system_prompt('es', 'You are a gardener in Málaga.')
        self.assertIn('You are a gardener in Málaga.', prompt)
        self.assertIn('Spanish', prompt)


class StripMarkdownFencesTest(TestCase):
    def test_strips_json_fence(self):
        text = '```json\n[{"a": 1}]\n```'
        self.assertEqual(_strip_markdown_fences(text), '[{"a": 1}]')

    def test_strips_plain_fence(self):
        text = '```\n{"a": 1}\n```'
        self.assertEqual(_strip_markdown_fences(text), '{"a": 1}')

    def test_passthrough_plain_json(self):
        text = '{"a": 1}'
        self.assertEqual(_strip_markdown_fences(text), '{"a": 1}')

    def test_empty_string(self):
        self.assertEqual(_strip_markdown_fences(''), '')


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
    def test_generate_item_description_handles_markdown_wrapped_json(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = (
            '```json\n{"description": "A rose", "cares": "Water daily"}\n```'
        )
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.generate_item_description('Rose', 'plant')

        self.assertEqual(result['description'], 'A rose')
        self.assertEqual(result['cares'], 'Water daily')

    @patch('apps.llm.service.get_llm_provider')
    def test_generate_item_description_handles_empty_response(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = ''
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.generate_item_description('Rose', 'plant')

        self.assertEqual(result['description'], '')
        self.assertEqual(result['cares'], '')

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
    def test_generate_care_schedule_handles_markdown_wrapped_json(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = (
            '```json\n[{"title": "Water", "event_type": "watering", '
            '"recurrence": "weekly", "days_from_now": 1, "description": ""}]\n```'
        )
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
    def test_generate_care_schedule_handles_empty_response(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = ''
        mock_get_provider.return_value = mock_provider

        mock_item = MagicMock()
        mock_item.name = 'Rose'
        mock_item.type = 'plant'
        mock_item.description = ''
        mock_item.cares = ''

        service = GardenLLMService()
        events = service.generate_care_schedule(mock_item)
        self.assertEqual(events, [])

    @patch('apps.llm.service.get_llm_provider')
    def test_generate_care_schedule_uses_fallback_when_description_empty(self, mock_get_provider):
        """Schedule generation should not send empty description to LLM."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = '[]'
        mock_get_provider.return_value = mock_provider

        mock_item = MagicMock()
        mock_item.name = 'Lavender'
        mock_item.type = 'plant'
        mock_item.description = ''
        mock_item.cares = ''

        service = GardenLLMService()
        service.generate_care_schedule(mock_item)

        call_args = mock_provider.generate.call_args[0][0]
        self.assertIn('A plant called Lavender', call_args)

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


class IdentifyPlantPromptTest(TestCase):
    def test_identification_prompt_requests_all_fields(self):
        from apps.llm.prompts import PLANT_IDENTIFICATION_PROMPT
        for field in ('name', 'type', 'description', 'cares'):
            self.assertIn(field, PLANT_IDENTIFICATION_PROMPT)
        self.assertIn('JSON', PLANT_IDENTIFICATION_PROMPT)
        for choice in ('plant', 'tree', 'shrub', 'other'):
            self.assertIn(choice, PLANT_IDENTIFICATION_PROMPT)


class IdentifyPlantTest(TestCase):
    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_success(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'name': 'Lavender',
            'type': 'shrub',
            'description': 'Fragrant flowering shrub',
            'cares': 'Full sun, water sparingly',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertEqual(result['name'], 'Lavender')
        self.assertEqual(result['type'], 'shrub')
        self.assertEqual(result['description'], 'Fragrant flowering shrub')
        self.assertEqual(result['cares'], 'Full sun, water sparingly')
        self.assertEqual(result['error'], '')
        # The image must be passed to the provider, along with a real prompt
        self.assertEqual(mock_provider.generate.call_args.kwargs['image_path'], '/tmp/photo.jpg')
        self.assertNotEqual(mock_provider.generate.call_args.args[0], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_handles_markdown_fenced_json(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = (
            '```json\n{"name": "Rose", "type": "plant", '
            '"description": "A rose", "cares": "Water weekly"}\n```'
        )
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertEqual(result['name'], 'Rose')
        self.assertEqual(result['error'], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_invalid_json_returns_error(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = 'not valid json'
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertNotEqual(result['error'], '')
        self.assertEqual(result['name'], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_coerces_invalid_type_to_plant(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'name': 'Tulip', 'type': 'Flower',
            'description': 'd', 'cares': 'c',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertEqual(result['type'], 'plant')
        self.assertEqual(result['error'], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_provider_exception_returns_error(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception('API error')
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertNotEqual(result['error'], '')

    @patch('apps.llm.service.get_llm_provider')
    def test_identify_plant_vision_not_supported_returns_readable_error(self, mock_get_provider):
        from apps.llm.providers import VisionNotSupportedError
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = VisionNotSupportedError(
            'Ollama provider does not support image input yet'
        )
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        result = service.identify_plant('/tmp/photo.jpg')

        self.assertIn('does not support image input', result['error'])


class GardenLLMServiceLanguageTest(TestCase):
    @patch('apps.llm.service.get_llm_provider')
    def test_service_passes_language_to_system_prompt(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'description': 'Una rosa',
            'cares': 'Regar a menudo',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService(language='es')
        service.generate_item_description('Rosa', 'plant')

        system_prompt = mock_provider.generate.call_args.kwargs['system']
        self.assertIn('Spanish', system_prompt)

    @patch('apps.llm.service.get_llm_provider')
    def test_service_defaults_to_english(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'description': 'A rose',
            'cares': 'Water weekly',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService()
        service.generate_item_description('Rose', 'plant')

        system_prompt = mock_provider.generate.call_args.kwargs['system']
        self.assertIn('in English', system_prompt)

    @patch('apps.llm.service.get_llm_provider')
    def test_service_uses_custom_gardener_prompt(self, mock_get_provider):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = json.dumps({
            'description': 'A rose',
            'cares': 'Water weekly',
        })
        mock_get_provider.return_value = mock_provider

        service = GardenLLMService(
            language='en',
            gardener_prompt='You are a gardener in Málaga, Mediterranean climate.',
        )
        service.generate_item_description('Rose', 'plant')

        system_prompt = mock_provider.generate.call_args.kwargs['system']
        self.assertIn('You are a gardener in Málaga, Mediterranean climate.', system_prompt)
        self.assertNotIn('professional botanist', system_prompt)
        self.assertIn('in English', system_prompt)


class GenerateCareTaskLanguageTest(TestCase):
    @patch('apps.llm.service.GardenLLMService')
    def test_task_uses_language_from_app_setting(self, mock_service_cls):
        from apps.garden.models import GardenItem
        from apps.llm import tasks

        mock_service_cls.return_value.generate_item_description.return_value = {
            'description': '',
            'cares': '',
        }
        mock_service_cls.return_value.generate_care_schedule.return_value = []

        AppSetting.set_language('es')
        item = GardenItem.objects.create(name='Rosa', type='plant')

        tasks.generate_item_care_async(item.pk)

        mock_service_cls.assert_called_once_with(language='es', gardener_prompt='')

    @patch('apps.llm.service.GardenLLMService')
    def test_task_passes_custom_gardener_prompt(self, mock_service_cls):
        from apps.garden.models import GardenItem
        from apps.llm import tasks

        mock_service_cls.return_value.generate_item_description.return_value = {
            'description': '',
            'cares': '',
        }
        mock_service_cls.return_value.generate_care_schedule.return_value = []

        custom = 'You are a gardener in Málaga, Mediterranean climate.'
        setting = AppSetting.current()
        setting.gardener_prompt = custom
        setting.save(update_fields=['gardener_prompt'])

        item = GardenItem.objects.create(name='Rosa', type='plant')

        tasks.generate_item_care_async(item.pk)

        mock_service_cls.assert_called_once_with(
            language='en', gardener_prompt=custom
        )
