import io
import shutil
import tempfile
from datetime import date, timedelta

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


class ListCareEventsTest(ToolTestBase):
    def _event(self, **kwargs):
        defaults = dict(item=self.rose, title='t', date=date.today(),
                        recurrence='once', event_type='watering')
        defaults.update(kwargs)
        return CalendarEvent.objects.create(**defaults)

    def test_default_window_excludes_past(self):
        self._event(date=date.today() - timedelta(days=1))
        self._event(date=date.today())
        self._event(date=date.today() + timedelta(days=180))
        self._event(date=date.today() + timedelta(days=181))
        result = tools.list_care_events()
        dates = [e['date'] for e in result['events']]
        # 3 in window: 'Water Rose' (today, from setUp) + today + +180; -1 and +181 excluded
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates, sorted(dates))

    def test_explicit_range_is_inclusive(self):
        # Oak has no setUp events, so the count is date-independent.
        self._event(item=self.oak, date=date(2026, 11, 1))
        self._event(item=self.oak, date=date(2026, 11, 14))
        self._event(item=self.oak, date=date(2026, 11, 15))
        result = tools.list_care_events(
            item_id=self.oak.pk, from_date='2026-11-01', to_date='2026-11-14')
        self.assertEqual(result['count'], 2)

    def test_filters_by_item_and_event_type(self):
        self._event(item=self.oak, event_type='fertilizing')
        self._event(event_type='pruning')
        result = tools.list_care_events(item_id=self.rose.pk, event_type='watering')
        self.assertEqual([e['title'] for e in result['events']], ['Water Rose'])

    def test_events_include_item_name(self):
        result = tools.list_care_events()
        self.assertEqual(result['events'][0]['item_name'], 'Rose')

    def test_bad_date_returns_error(self):
        self.assertEqual(
            tools.list_care_events(from_date='14/11/2026'),
            {'error': "Invalid date '14/11/2026': use YYYY-MM-DD"})

    def test_unknown_item_returns_error(self):
        self.assertEqual(
            tools.list_care_events(item_id=9999),
            {'error': 'Garden item 9999 not found'})

    def test_truncates_over_100(self):
        for n in range(101):
            self._event(date=date.today() + timedelta(days=n), title=f'e{n}')
        result = tools.list_care_events()
        self.assertEqual(result['count'], 102)  # 101 new + 'Water Rose'
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['events']), 100)


class AddCareEventTest(ToolTestBase):
    def test_creates_event(self):
        result = tools.add_care_event(
            self.rose.pk, 'Deep Water', '2026-12-01', 'watering',
            recurrence='monthly', description='Soak the root zone.')
        self.assertEqual(result['status'], 'created')
        event = CalendarEvent.objects.get(pk=result['id'])
        self.assertEqual(event.title, 'Deep Water')
        self.assertEqual(str(event.date), '2026-12-01')
        self.assertEqual(event.recurrence, 'monthly')
        self.assertTrue(event.is_manual)

    def test_unknown_item_error(self):
        self.assertEqual(
            tools.add_care_event(9999, 't', '2026-12-01', 'watering'),
            {'error': 'Garden item 9999 not found'})

    def test_invalid_date_error(self):
        result = tools.add_care_event(self.rose.pk, 't', 'dec 1', 'watering')
        self.assertEqual(result, {'error': "Invalid date 'dec 1': use YYYY-MM-DD"})

    def test_blank_title_error(self):
        result = tools.add_care_event(self.rose.pk, '   ', '2026-12-01', 'watering')
        self.assertEqual(result, {'error': 'Title must not be blank'})

    def test_invalid_event_type_error(self):
        result = tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'weeding')
        self.assertEqual(
            result,
            {'error': "Invalid event_type 'weeding'. Valid: watering, fertilizing, pruning, other"})

    def test_invalid_recurrence_error(self):
        result = tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'watering', recurrence='daily')
        self.assertEqual(
            result, {'error': "Invalid recurrence 'daily'. Valid: once, weekly, monthly, yearly"})

    def test_recurring_event_expands_occurrences(self):
        result = tools.add_care_event(
            self.rose.pk, 'Weekly Water', (date.today() + timedelta(days=1)).isoformat(),
            'watering', recurrence='weekly')
        base = CalendarEvent.objects.get(pk=result['id'])
        occurrences = list(CalendarEvent.objects.filter(parent_event=base))
        self.assertGreater(len(occurrences), 0)
        self.assertTrue(all(o.date > base.date for o in occurrences))
        # occurrences are manual too, so care regeneration preserves the recurrence
        self.assertTrue(all(o.is_manual for o in occurrences))

    def test_no_rows_created_on_errors(self):
        for call in (
            lambda: tools.add_care_event(9999, 't', '2026-12-01', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, 't', 'bad', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, '', '2026-12-01', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'weeding'),
            lambda: tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'watering', recurrence='daily'),
        ):
            call()
        self.assertEqual(CalendarEvent.objects.count(), 1)  # only 'Water Rose' from setUp
