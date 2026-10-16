import os
import shutil
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from PIL import Image

from apps.garden.models import GardenItem
from apps.garden.tests.test_images import make_noise_jpeg


class PhotoUploadTest(APITestCase):
    """Uploaded photos must be stored optimized, not as the raw phone file."""

    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='gardener-test-media-')
        self._media_ctx = override_settings(MEDIA_ROOT=self.media_root)
        self._media_ctx.__enter__()

    def tearDown(self):
        self._media_ctx.__exit__(None, None, None)
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _open_stored(self, item):
        return Image.open(item.photo.path)

    @patch('apps.garden.signals.on_garden_item_created')
    def test_create_with_large_photo_is_stored_optimized(self, _):
        original = make_noise_jpeg(3000, 4000)
        data = {
            'name': 'Oak',
            'type': 'tree',
            'photo': SimpleUploadedFile('oak.jpg', original, 'image/jpeg'),
        }
        response = self.client.post('/api/v1/garden/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = GardenItem.objects.get(name='Oak')
        img = self._open_stored(item)
        self.assertLessEqual(max(img.size), 1600)
        self.assertLess(os.path.getsize(item.photo.path), len(original) // 2)

    @patch('apps.garden.signals.on_garden_item_created')
    def test_small_photo_upload_is_stored_unchanged(self, _):
        original = make_noise_jpeg(400, 300, quality=75)
        self.assertLess(len(original), 512_000)
        data = {
            'name': 'Fern',
            'type': 'plant',
            'photo': SimpleUploadedFile('fern.jpg', original, 'image/jpeg'),
        }
        response = self.client.post('/api/v1/garden/', data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = GardenItem.objects.get(name='Fern')
        with open(item.photo.path, 'rb') as f:
            self.assertEqual(f.read(), original)

    def test_replace_photo_is_stored_optimized(self):
        item = GardenItem.objects.create(name='Rose', type='plant')
        original = make_noise_jpeg(4000, 3000)
        data = {'photo': SimpleUploadedFile('rose.jpg', original, 'image/jpeg')}
        response = self.client.patch(
            f'/api/v1/garden/{item.pk}/', data, format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        img = self._open_stored(item)
        self.assertLessEqual(max(img.size), 1600)
        self.assertLess(os.path.getsize(item.photo.path), len(original) // 2)
