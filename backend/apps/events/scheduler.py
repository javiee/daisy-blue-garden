from datetime import date, timedelta
from django.db import models
from .models import CalendarEvent
import calendar

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MAX_REPEATED_YEARS = 5


def _add_years(d: date, years: int) -> date:
    """d + years, clamping Feb 29 to Feb 28 on non-leap years."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _next_date(base_event: CalendarEvent, current: date) -> date:
    if base_event.recurrence == 'weekly':
        return current + timedelta(weeks=1)
    if base_event.recurrence == 'monthly':
        m = current.month + 1
        y = current.year
        if m > 12:
            m = 1
            y += 1
        day = min(current.day, DAYS_IN_MONTH[m - 1])
        return current.replace(year=y, month=m, day=day)
    if base_event.recurrence == 'yearly':
        return current.replace(year=current.year + 1)
    # 'once' with repeats_yearly behaves as a yearly series
    return current.replace(year=current.year + 1)


def expand_all_recurring_events(months_ahead: int = 6):
    """Expand future occurrences for all recurring events. Safe to call repeatedly."""
    recurring = CalendarEvent.objects.filter(
        models.Q(recurrence__ne='once') | models.Q(recurrence='once', repeats_yearly=True),
        parent_event__isnull=True,
    )
    for event in recurring:
        generate_recurring_events(event, months_ahead=months_ahead)


def generate_recurring_events(base_event: CalendarEvent, months_ahead: int = 6) -> list[CalendarEvent]:
    """
    Given a CalendarEvent with recurrence, create future occurrences.
    Returns the list of newly created CalendarEvent objects.

    Occurrences are capped at ~months_ahead from today. When
    repeats_yearly is set, a weekly/monthly series restarts its
    start->end_date window each year (and a 'once' event repeats on the
    same date each year); the daily re-expansion task materializes next
    year's window as it approaches the cap.
    """
    if base_event.recurrence == 'once' and not base_event.repeats_yearly:
        return []

    created = []

    # Calculate cap (last day of today + months_ahead)
    month = date.today().month + months_ahead
    year = date.today().year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    cap = date(year, month, calendar.monthrange(year, month)[1])

    # Window end for this year. 'yearly' honors end_date (stops there,
    # never wraps); 'once' ignores it.
    window_end = None
    if base_event.recurrence in ('weekly', 'monthly', 'yearly'):
        window_end = base_event.end_date

    # For repeating windows, skip years whose window is already fully in
    # the past so old base events don't waste the wrap budget on history.
    year_offset = 0
    if (window_end is not None and base_event.repeats_yearly
            and base_event.recurrence != 'yearly'):
        year_offset = max(0, cap.year - base_event.date.year - 1)

    current_date = _add_years(base_event.date, year_offset)
    if window_end is not None:
        window_end = _add_years(window_end, year_offset)

    years_repeated = 0

    while True:
        next_date = _next_date(base_event, current_date)

        if next_date >= cap:
            break

        if window_end is not None and next_date >= window_end:
            if base_event.repeats_yearly and base_event.recurrence != 'yearly':
                years_repeated += 1
                if years_repeated > MAX_REPEATED_YEARS:
                    break
                window_end = _add_years(window_end, 1)
                # restart the window at its start date in the next year
                current_date = _add_years(base_event.date, year_offset + years_repeated)
                continue
            break

        event, created_flag = CalendarEvent.objects.get_or_create(
            item=base_event.item,
            title=base_event.title,
            date=next_date,
            recurrence=base_event.recurrence,
            parent_event=base_event,
            event_type=base_event.event_type,
            defaults={'description': base_event.description},
        )
        if created_flag:
            created.append(event)
        current_date = next_date

        if len(created) > 100:  # safety limit
            break

    return created
