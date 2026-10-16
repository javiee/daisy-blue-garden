import os
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import override_settings, TestCase
from io import StringIO

from PIL import Image

from apps.garden.models import GardenItem
from apps.garden.tests.test_images import make_noise_jpeg


class OptimizePhotosCommandTest(TestCase):
    """`manage.py optimize_photos` shrinks stored photos in place, idempotently."""

    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='gardener-test-media-')
        self._media_ctx = override_settings(MEDIA_ROOT=self.media_root)
        self._media_ctx.__enter__()

    def tearDown(self):
        self._media_ctx.__exit__(None, None, None)
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_item_with_photo(self, name='oak.jpg', width=3000, height=4000):
        original = make_noise_jpeg(width, height)
        item = GardenItem.objects.create(name='Oak', type='tree')
        item.photo.save(name, ContentFile(original), save=False)
        item.save()
        return item, original

    def _run(self):
        out = StringIO()
        call_command('optimize_photos', stdout=out)
        return out.getvalue()

    def test_optimizes_stored_photo_in_place(self):
        item, original = self._create_item_with_photo()
        photo_name = item.photo.name

        self._run()

        item.refresh_from_db()
        self.assertEqual(item.photo.name, photo_name)  # filename/URL unchanged
        with open(item.photo.path, 'rb') as f:
            stored = f.read()
        img = Image.open(item.photo.path)
        self.assertLessEqual(max(img.size), 1600)
        self.assertLess(len(stored), len(original) // 2)

    def test_second_run_is_a_noop(self):
        item, _ = self._create_item_with_photo()

        self._run()
        with open(item.photo.path, 'rb') as f:
            first_pass = f.read()
        self._run()
        with open(item.photo.path, 'rb') as f:
            second_pass = f.read()

        self.assertEqual(second_pass, first_pass)

    def test_small_photo_is_untouched(self):
        original = make_noise_jpeg(400, 300, quality=75)
        item = GardenItem.objects.create(name='Fern', type='plant')
        item.photo.save('fern.jpg', ContentFile(original), save=False)
        item.save()

        self._run()

        with open(item.photo.path, 'rb') as f:
            self.assertEqual(f.read(), original)

    def test_skips_items_without_photo(self):
        GardenItem.objects.create(name='Seedling', type='plant')
        self._run()  # must not raise
