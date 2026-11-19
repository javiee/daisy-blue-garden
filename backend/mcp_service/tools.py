"""Plain Django ORM functions backing the MCP tools.

Each function returns a JSON-serializable dict. Failures are returned as
``{"error": "<message>"}`` dicts, never raised: the MCP SDK replaces a raised
exception's message with a generic "Error executing tool <name>".
"""
from django.conf import settings
from django.db.models import Count, Q

from apps.events.models import CalendarEvent
from apps.garden.models import GardenItem

GARDEN_ITEMS_CAP = 50


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
