import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from PIL import Image


class GenerateItemCareAsyncTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')

    @patch('apps.llm.service.GardenLLMService')
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
        self.assertTrue(CalendarEvent.objects.filter(item=self.item).exists())
        event = CalendarEvent.objects.filter(item=self.item).first()
        self.assertEqual(event.event_type, 'watering')
        self.assertEqual(event.item, self.item)

    @patch('apps.llm.service.GardenLLMService')
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


class GenerateItemCareSkipWhenPopulatedTest(TestCase):
    @patch('apps.llm.service.GardenLLMService')
    def test_skips_description_when_both_already_populated(self, mock_service_cls):
        """Vision-generated description/cares must not be clobbered on item create."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.generate_care_schedule.return_value = []
        item = GardenItem.objects.create(
            name='Rose', type='plant',
            description='A rose identified from a photo',
            cares='Water weekly, full sun',
        )

        from apps.llm.tasks import generate_item_care_async
        generate_item_care_async(item.pk)

        item.refresh_from_db()
        self.assertEqual(item.description, 'A rose identified from a photo')
        self.assertEqual(item.cares, 'Water weekly, full sun')
        mock_service.generate_item_description.assert_not_called()
        # The care schedule is still generated, from the existing text
        mock_service.generate_care_schedule.assert_called_once()

    @patch('apps.llm.service.GardenLLMService')
    def test_still_generates_when_only_one_field_populated(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.generate_item_description.return_value = {
            'description': 'A rose', 'cares': 'Water weekly',
        }
        mock_service.generate_care_schedule.return_value = []
        item = GardenItem.objects.create(name='Rose', type='plant', description='A rose', cares='')

        from apps.llm.tasks import generate_item_care_async
        generate_item_care_async(item.pk)

        mock_service.generate_item_description.assert_called_once()
        item.refresh_from_db()
        self.assertEqual(item.cares, 'Water weekly')


def _make_test_image() -> bytes:
    import io
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), color='green').save(buf, format='JPEG')
    return buf.getvalue()


class IdentifyPlantAsyncTest(TestCase):
    def setUp(self):
        from apps.llm.models import PlantIdentification
        self._media_root = tempfile.mkdtemp(prefix='llm-identify-')
        self.override = override_settings(MEDIA_ROOT=self._media_root)
        self.override.enable()
        self.identification = PlantIdentification.objects.create()
        self.identification.photo.save('test.jpg', ContentFile(_make_test_image()), save=True)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)

    @patch('apps.llm.service.GardenLLMService')
    def test_success_updates_record(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.identify_plant.return_value = {
            'name': 'Rose', 'type': 'plant',
            'description': 'A rose', 'cares': 'Water weekly', 'error': '',
        }

        from apps.llm.tasks import identify_plant_async
        status = identify_plant_async(self.identification.pk)

        self.identification.refresh_from_db()
        self.assertEqual(status, 'complete')
        self.assertEqual(self.identification.status, 'complete')
        self.assertEqual(self.identification.name, 'Rose')
        self.assertEqual(self.identification.type, 'plant')
        self.assertEqual(self.identification.description, 'A rose')
        self.assertEqual(self.identification.cares, 'Water weekly')
        self.assertEqual(self.identification.error, '')
        # The task must point the service at the stored photo
        self.assertEqual(
            mock_service.identify_plant.call_args.args[0],
            self.identification.photo.path,
        )

    @patch('apps.llm.service.GardenLLMService')
    def test_provider_error_marks_failed(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.identify_plant.return_value = {
            'name': '', 'type': '', 'description': '', 'cares': '',
            'error': 'Identification failed: API error',
        }

        from apps.llm.tasks import identify_plant_async
        status = identify_plant_async(self.identification.pk)

        self.identification.refresh_from_db()
        self.assertEqual(status, 'failed')
        self.assertEqual(self.identification.status, 'failed')
        self.assertIn('API error', self.identification.error)
        self.assertEqual(self.identification.name, '')

    @patch('apps.llm.service.GardenLLMService')
    def test_unidentifiable_photo_marks_failed(self, mock_service_cls):
        """A successful LLM call that names nothing is a failure for the user."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.identify_plant.return_value = {
            'name': '', 'type': '', 'description': '', 'cares': '', 'error': '',
        }

        from apps.llm.tasks import identify_plant_async
        status = identify_plant_async(self.identification.pk)

        self.identification.refresh_from_db()
        self.assertEqual(status, 'failed')
        self.assertNotEqual(self.identification.error, '')
        self.assertEqual(self.identification.name, '')

    def test_missing_record_does_not_crash(self):
        from apps.llm.tasks import identify_plant_async
        result = identify_plant_async(99999)
        self.assertIsNone(result)
