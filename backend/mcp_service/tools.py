"""Plain Django ORM functions backing the MCP tools.

Each function returns a JSON-serializable dict. Failures are returned as
``{"error": "<message>"}`` dicts, never raised: the MCP SDK replaces a raised
exception's message with a generic "Error executing tool <name>".
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Count, Q

from apps.events.models import CalendarEvent
from apps.garden.models import GardenItem

GARDEN_ITEMS_CAP = 50
EVENTS_CAP = 100
DEFAULT_WINDOW_DAYS = 180
EVENT_TYPE_VALUES = [v for v, _ in CalendarEvent.EVENT_TYPE_CHOICES]
RECURRENCE_VALUES = [v for v, _ in CalendarEvent.RECURRENCE_CHOICES]


def _photo_url(item: GardenItem):
    if not item.photo:
        return None
    return f"{settings.PUBLIC_BASE_URL}/media/{item.photo.name}"


def _event_dict(event: CalendarEvent) -> dict:
    return {
        'id': event.pk,
        'title': event.title,
        'description': event.description,
        'date': event.date.isoformat(),
        'recurrence': event.recurrence,
        'event_type': event.event_type,
        'is_manual': event.is_manual,
    }


def list_garden_items(type: str | None = None, search: str | None = None) -> dict:
    qs = GardenItem.objects.annotate(event_count=Count('events'))
    if type:
        qs = qs.filter(type=type)
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(type__icontains=search)
            | Q(description__icontains=search)
        )
    count = qs.count()
    items = [
        {
            'id': item.pk,
            'name': item.name,
            'type': item.type,
            'description': item.description,
            'cares': item.cares,
            'photo_url': _photo_url(item),
            'event_count': item.event_count,
        }
        for item in qs[:GARDEN_ITEMS_CAP]
    ]
    return {'count': count, 'truncated': count > GARDEN_ITEMS_CAP, 'items': items}


def _parse_date(value: str):
    """Parse a YYYY-MM-DD string; raise ValueError on anything else."""
    return datetime.strptime(value, '%Y-%m-%d').date()


def list_care_events(item_id: int | None = None, event_type: str | None = None,
                     from_date: str | None = None, to_date: str | None = None) -> dict:
    try:
        from_d = _parse_date(from_date) if from_date else None
        to_d = _parse_date(to_date) if to_date else None
    except ValueError:
        bad = from_date if (from_date and not to_date) else to_date
        return {'error': f"Invalid date '{bad}': use YYYY-MM-DD"}

    qs = CalendarEvent.objects.select_related('item')
    if item_id is not None:
        if not GardenItem.objects.filter(pk=item_id).exists():
            return {'error': f'Garden item {item_id} not found'}
        qs = qs.filter(item_id=item_id)
    if event_type is not None:
        if event_type not in EVENT_TYPE_VALUES:
            return {'error': f"Invalid event_type '{event_type}'. Valid: "
                             + ', '.join(EVENT_TYPE_VALUES)}
        qs = qs.filter(event_type=event_type)
    if from_d is not None:
        qs = qs.filter(date__gte=from_d)
    if to_d is not None:
        qs = qs.filter(date__lte=to_d)
    if from_d is None and to_d is None:
        today = datetime.now().date()
        qs = qs.filter(date__gte=today, date__lte=today + timedelta(days=DEFAULT_WINDOW_DAYS))

    count = qs.count()
    events = [
        {
            'id': e.pk,
            'item_id': e.item_id,
            'item_name': e.item.name,
            'title': e.title,
            'description': e.description,
            'date': e.date.isoformat(),
            'recurrence': e.recurrence,
            'event_type': e.event_type,
            'is_manual': e.is_manual,
        }
        for e in qs[:EVENTS_CAP]
    ]
    return {'count': count, 'truncated': count > EVENTS_CAP, 'events': events}


def add_care_event(item_id: int, title: str, date: str, event_type: str,
                   recurrence: str = 'once', description: str = '') -> dict:
    if not GardenItem.objects.filter(pk=item_id).exists():
        return {'error': f'Garden item {item_id} not found'}
    try:
        event_date = _parse_date(date)
    except ValueError:
        return {'error': f"Invalid date '{date}': use YYYY-MM-DD"}
    if not title.strip():
        return {'error': 'Title must not be blank'}
    if event_type not in EVENT_TYPE_VALUES:
        return {'error': f"Invalid event_type '{event_type}'. Valid: "
                         + ', '.join(EVENT_TYPE_VALUES)}
    if recurrence not in RECURRENCE_VALUES:
        return {'error': f"Invalid recurrence '{recurrence}'. Valid: "
                         + ', '.join(RECURRENCE_VALUES)}

    event = CalendarEvent.objects.create(
        item_id=item_id, title=title, date=event_date, event_type=event_type,
        recurrence=recurrence, description=description, is_manual=True,
    )
    return {
        'status': 'created',
        'id': event.pk,
        'item_id': item_id,
        'item_name': event.item.name,
        'title': event.title,
        'description': event.description,
        'date': event.date.isoformat(),
        'recurrence': event.recurrence,
        'event_type': event.event_type,
        'is_manual': event.is_manual,
    }


def get_garden_item(item_id: int) -> dict:
    item = GardenItem.objects.filter(pk=item_id).first()
    if item is None:
        return {'error': f'Garden item {item_id} not found'}
    return {
        'id': item.pk,
        'name': item.name,
        'type': item.type,
        'description': item.description,
        'cares': item.cares,
        'photo_url': _photo_url(item),
        'created_at': item.created_at.date().isoformat(),
        'updated_at': item.updated_at.date().isoformat(),
        'events': [_event_dict(e) for e in item.events.all()],
    }
