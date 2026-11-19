import io
import shutil
import tempfile
from datetime import date

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.events.models import CalendarEvent
from apps.garden.models import GardenItem
from mcp_service import tools


def make_tiny_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'green').save(buf, 'JPEG')
    return buf.getvalue()


class ToolTestBase(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='mcp-test-media-')
        self._media_ctx = override_settings(MEDIA_ROOT=self.media_root)
        self._media_ctx.__enter__()
        self.rose = GardenItem.objects.create(
            name='Rose', type='plant', description='Classic garden shrub.',
            cares='Water twice a week. Prefers full sun, well-drained soil.')
        self.oak = GardenItem.objects.create(name='Oak', type='tree')
        self.oak.photo.save('oak.jpg', ContentFile(make_tiny_jpeg()), save=True)
        CalendarEvent.objects.create(
            item=self.rose, title='Water Rose', date=date.today(),
            recurrence='weekly', event_type='watering')

    def tearDown(self):
        self._media_ctx.__exit__(None, None, None)
        shutil.rmtree(self.media_root, ignore_errors=True)


class ListGardenItemsTest(ToolTestBase):
    def test_returns_all_with_fields(self):
        result = tools.list_garden_items()
        self.assertEqual(result['count'], 2)
        self.assertFalse(result['truncated'])
        self.assertEqual(len(result['items']), 2)
        rose = next(i for i in result['items'] if i['name'] == 'Rose')
        self.assertEqual(
            set(rose), {'id', 'name', 'type', 'description', 'cares', 'photo_url', 'event_count'})
        self.assertEqual(rose['photo_url'], None)
        self.assertEqual(rose['event_count'], 1)

    def test_photo_url_is_absolute(self):
        result = tools.list_garden_items()
        oak = next(i for i in result['items'] if i['name'] == 'Oak')
        self.assertEqual(oak['photo_url'], 'http://localhost:8000/media/garden/oak.jpg')

    def test_filters_by_type(self):
        result = tools.list_garden_items(type='tree')
        self.assertEqual([i['name'] for i in result['items']], ['Oak'])

    def test_search_matches_name_and_description(self):
        self.assertEqual(len(tools.list_garden_items(search='rose')['items']), 1)
        # 'shrub' appears only in Rose's description, not in any name or type
        self.assertEqual(len(tools.list_garden_items(search='shrub')['items']), 1)
        self.assertEqual(tools.list_garden_items(search='zzz')['count'], 0)

    def test_truncates_over_50(self):
        for n in range(49):
            GardenItem.objects.create(name=f'Filler {n}', type='plant')
        result = tools.list_garden_items()
        self.assertEqual(result['count'], 51)
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['items']), 50)


class GetGardenItemTest(ToolTestBase):
    def test_found_includes_events(self):
        result = tools.get_garden_item(self.rose.pk)
        self.assertEqual(result['name'], 'Rose')
        self.assertEqual(result['events'][0]['title'], 'Water Rose')
        self.assertEqual(result['events'][0]['event_type'], 'watering')
        self.assertRegex(result['created_at'], r'^\d{4}-\d{2}-\d{2}$')  # date-only ISO

    def test_not_found_returns_error_dict(self):
        result = tools.get_garden_item(9999)
        self.assertEqual(result, {'error': 'Garden item 9999 not found'})
