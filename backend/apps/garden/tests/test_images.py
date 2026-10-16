import io
import os
import shutil
import tempfile

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from PIL import Image, ImageOps

from apps.garden.images import MAX_LONGEST_EDGE, optimize_image_file


def make_noise_jpeg(width, height, quality=95, orientation=None):
    """Build a JPEG with incompressible noise (like a phone photo) as bytes."""
    img = Image.effect_noise((width, height), 30).convert('RGB')
    buf = io.BytesIO()
    save_kwargs = {'quality': quality, 'optimize': True}
    if orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = orientation
        save_kwargs['exif'] = exif
    img.save(buf, 'JPEG', **save_kwargs)
    return buf.getvalue()


def image_from_bytes(data):
    return Image.open(io.BytesIO(data))


class OptimizeImageFileTest(TestCase):
    def test_downscales_large_image_to_max_longest_edge(self):
        original = make_noise_jpeg(3000, 4000)
        result = optimize_image_file(ContentFile(original, name='big.jpg'))

        self.assertEqual(result.name, 'big.jpg')
        data = result.read()
        img = image_from_bytes(data)
        self.assertEqual(img.size, (1200, 1600))
        self.assertLess(len(data), len(original) // 2)

    def test_applies_exif_orientation_and_strips_exif(self):
        original = make_noise_jpeg(3000, 4000, orientation=6)  # rotate 90 CW
        result = optimize_image_file(ContentFile(original, name='phone.jpg'))

        img = image_from_bytes(result.read())
        self.assertEqual(img.size, (1600, 1200))
        exif = img.getexif()
        self.assertNotIn(0x0112, exif)

    def test_small_image_passes_through_unchanged(self):
        original = make_noise_jpeg(400, 300, quality=75)
        self.assertLess(len(original), 512_000)
        content = ContentFile(original, name='small.jpg')
        result = optimize_image_file(content)

        self.assertIs(result, content)
        self.assertEqual(result.read(), original)  # stream must be rewound

    def test_small_dimensions_but_large_file_is_recompressed(self):
        original = make_noise_jpeg(1500, 1500, quality=95)
        self.assertGreater(len(original), 512_000)
        result = optimize_image_file(ContentFile(original, name='chunky.jpg'))

        data = result.read()
        img = image_from_bytes(data)
        self.assertEqual(img.size, (1500, 1500))
        self.assertLess(len(data), len(original))
