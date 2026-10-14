from datetime import date
from unittest import mock
from django.test import TestCase
from apps.garden.models import GardenItem
from apps.events.models import CalendarEvent
from apps.events import scheduler
from apps.events.scheduler import generate_recurring_events


class FrozenDate(date):
    """date with a frozen today() so the 6-month cap is deterministic."""

    @classmethod
    def today(cls):
        return cls(2026, 10, 7)


class RecurringExpansionTest(TestCase):
    def setUp(self):
        self.item = GardenItem.objects.create(name='Rose', type='plant')

    def _expand(self, base):
        with mock.patch.object(scheduler, 'date', FrozenDate):
            return generate_recurring_events(base, months_ahead=6)

    def _occurrence_dates(self, base):
        return set(CalendarEvent.objects.filter(parent_event=base).values_list('date', flat=True))

    def test_monthly_window_repeats_each_year(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Fertilize', date=date(2026, 2, 15),
            recurrence='monthly', event_type='fertilizing',
            end_date=date(2026, 6, 30), repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        # current year window (base 02-15 + Feb->Jun)
        self.assertIn(date(2026, 3, 15), dates)
        self.assertIn(date(2026, 6, 15), dates)
        self.assertNotIn(date(2026, 7, 15), dates)
        # next year window, capped at 2027-04-30 (frozen today + 6 months)
        self.assertIn(date(2027, 3, 15), dates)
        self.assertIn(date(2027, 4, 15), dates)
        self.assertNotIn(date(2027, 5, 15), dates)

    def test_monthly_window_without_repeat_stops_at_end(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Fertilize', date=date(2026, 2, 15),
            recurrence='monthly', event_type='fertilizing',
            end_date=date(2026, 6, 30), repeats_yearly=False,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        self.assertIn(date(2026, 6, 15), dates)
        self.assertNotIn(date(2026, 7, 15), dates)
        self.assertNotIn(date(2027, 2, 15), dates)

    def test_weekly_window_repeats_next_year(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Water', date=date(2026, 2, 15),
            recurrence='weekly', event_type='watering',
            end_date=date(2026, 6, 30), repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        self.assertIn(date(2026, 6, 28), dates)
        self.assertNotIn(date(2026, 7, 5), dates)
        self.assertIn(date(2027, 2, 22), dates)
        self.assertIn(date(2027, 4, 26), dates)
        self.assertNotIn(date(2027, 5, 3), dates)  # beyond the 6-month cap

    def test_once_with_repeat_gets_next_year_occurrence(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Repot', date=date(2026, 3, 1),
            recurrence='once', event_type='other',
            repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        self.assertIn(date(2027, 3, 1), dates)
        self.assertNotIn(date(2028, 3, 1), dates)

    def test_once_without_repeat_has_no_occurrences(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Repot', date=date(2026, 3, 1),
            recurrence='once', event_type='other',
            repeats_yearly=False,
        )
        self._expand(base)
        self.assertEqual(self._occurrence_dates(base), set())

    def test_yearly_behavior_unchanged(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Prune', date=date(2026, 3, 1),
            recurrence='yearly', event_type='pruning',
            repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        self.assertIn(date(2027, 3, 1), dates)
        self.assertNotIn(date(2028, 3, 1), dates)

    def test_yearly_stops_at_end_date(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Prune', date=date(2026, 3, 1),
            recurrence='yearly', event_type='pruning',
            end_date=date(2026, 12, 31), repeats_yearly=True,
        )
        self._expand(base)
        self.assertEqual(self._occurrence_dates(base), set())

    def test_monthly_without_end_date_runs_until_cap(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Water', date=date(2026, 2, 15),
            recurrence='monthly', event_type='watering',
            repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        self.assertIn(date(2027, 4, 15), dates)
        self.assertNotIn(date(2027, 5, 15), dates)

    def test_old_base_event_still_materializes_next_window(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Fertilize', date=date(2024, 2, 15),
            recurrence='monthly', event_type='fertilizing',
            end_date=date(2024, 6, 30), repeats_yearly=True,
        )
        self._expand(base)
        dates = self._occurrence_dates(base)
        # frozen today 2026-10-07 -> next future window is Feb->Jun 2027
        self.assertIn(date(2027, 3, 15), dates)
        self.assertIn(date(2027, 4, 15), dates)
        self.assertNotIn(date(2027, 5, 15), dates)  # beyond the 6-month cap

    def test_expansion_is_idempotent(self):
        base = CalendarEvent.objects.create(
            item=self.item, title='Fertilize', date=date(2026, 2, 15),
            recurrence='monthly', event_type='fertilizing',
            end_date=date(2026, 6, 30), repeats_yearly=True,
        )
        self._expand(base)
        count = self._occurrence_dates(base)
        self._expand(base)
        self.assertEqual(self._occurrence_dates(base), count)
