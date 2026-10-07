import os
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from PIL import Image
from apps.llm.models import PlantIdentification


def _jpeg_upload(name='photo.jpg') -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new('RGB', (10, 10), color='green').save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class IdentifyPlantAPITest(APITestCase):
    def setUp(self):
        self._media_root = tempfile.mkdtemp(prefix='llm-identify-view-')
        self.override = override_settings(MEDIA_ROOT=self._media_root)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)

    @patch('apps.llm.views.async_task')
    def test_post_identify_creates_record_and_queues_task(self, mock_async_task):
        mock_async_task.return_value = 'task-123'
        response = self.client.post(
            '/api/v1/llm/identify/', {'photo': _jpeg_upload()}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = PlantIdentification.objects.first()
        self.assertIsNotNone(record)
        self.assertEqual(response.data['id'], record.pk)
        self.assertEqual(response.data['status'], 'pending')
        mock_async_task.assert_called_once_with(
            'apps.llm.tasks.identify_plant_async', record.pk
        )

    @patch('apps.llm.views.async_task')
    def test_post_identify_requires_photo(self, mock_async_task):
        response = self.client.post('/api/v1/llm/identify/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_async_task.assert_not_called()
        self.assertFalse(PlantIdentification.objects.exists())

    @patch('apps.llm.views.async_task')
    def test_post_identify_rejects_non_image_file(self, mock_async_task):
        evil = SimpleUploadedFile(
            'evil.html', b'<script>alert(1)</script>', content_type='text/html'
        )
        response = self.client.post(
            '/api/v1/llm/identify/', {'photo': evil}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PlantIdentification.objects.exists())
        mock_async_task.assert_not_called()

    @patch('apps.llm.views.async_task')
    def test_post_identify_rejects_oversized_photo(self, mock_async_task):
        big = SimpleUploadedFile(
            'big.jpg', b'\x00' * (11 * 1024 * 1024), content_type='image/jpeg'
        )
        response = self.client.post(
            '/api/v1/llm/identify/', {'photo': big}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(PlantIdentification.objects.exists())
        mock_async_task.assert_not_called()

    @patch('apps.llm.views.async_task')
    def test_post_identify_sweeps_abandoned_records(self, mock_async_task):
        """Records abandoned by the client (older than 1h) are deleted, with their file."""
        mock_async_task.return_value = 'task-123'
        abandoned = PlantIdentification.objects.create()
        abandoned.photo.save('old.jpg', ContentFile(_jpeg_upload().read()), save=True)
        photo_path = abandoned.photo.path
        PlantIdentification.objects.filter(pk=abandoned.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        response = self.client.post(
            '/api/v1/llm/identify/', {'photo': _jpeg_upload()}, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(PlantIdentification.objects.filter(pk=abandoned.pk).exists())
        self.assertFalse(os.path.exists(photo_path))
        self.assertEqual(PlantIdentification.objects.count(), 1)

    def test_get_identification_returns_fields(self):
        record = PlantIdentification.objects.create(
            status='complete', name='Rose', type='plant',
            description='A rose', cares='Water weekly',
        )
        response = self.client.get(f'/api/v1/llm/identify/{record.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'complete')
        self.assertEqual(response.data['name'], 'Rose')
        self.assertEqual(response.data['type'], 'plant')
        self.assertEqual(response.data['cares'], 'Water weekly')

    def test_get_identification_404(self):
        response = self.client.get('/api/v1/llm/identify/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_identification_removes_record_and_file(self):
        record = PlantIdentification.objects.create()
        record.photo.save('x.jpg', ContentFile(_jpeg_upload().read()), save=True)
        photo_path = record.photo.path
        self.assertTrue(os.path.exists(photo_path))

        response = self.client.delete(f'/api/v1/llm/identify/{record.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PlantIdentification.objects.exists())
        self.assertFalse(os.path.exists(photo_path))

    def test_delete_identification_404(self):
        response = self.client.delete('/api/v1/llm/identify/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
