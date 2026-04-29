from datetime import date, timedelta
from .models import CalendarEvent
import calendar

def expand_all_recurring_events(months_ahead: int = 6):
    """Expand future occurrences for all recurring events. Safe to call repeatedly."""
    recurring =  CalendarEvent.objects.filter(parent_event__isnull=True).exclude(recurrence='once')
    for event in recurring:
        generate_recurring_events(event, months_ahead=months_ahead)

def generate_recurring_events(base_event: CalendarEvent, months_ahead: int = 6) -> list[CalendarEvent]:
    """
    Given a CalendarEvent with recurrence, create future occurrences.
    Returns the list of newly created CalendarEvent objects.
    """
    if base_event.recurrence == 'once':
        return []

    created = []
    current_date = base_event.date

    # Calculate end date (months_ahead from now)
    month = date.today().month + months_ahead
    year = date.today().year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    if base_event.end_date and base_event.end_date < end_date:
        end_date = base_event.end_date

    while True:
        if base_event.recurrence == 'weekly':
            next_date = current_date + timedelta(weeks=1)
        elif base_event.recurrence == 'monthly':
            m = current_date.month + 1
            y = current_date.year
            if m > 12:
                m = 1
                y += 1
            day = min(current_date.day, [31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
            next_date = current_date.replace(year=y, month=m, day=day)
        elif base_event.recurrence == 'yearly':
            next_date = current_date.replace(year=current_date.year + 1)
        else:
            break

        if next_date >= end_date:
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
