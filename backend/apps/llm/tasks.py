import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

def generate_item_care_async(item_id: int):
    """
    1. Fetch GardenItem
    2. Call LLM to generate description and cares
    3. Update item (without re-triggering signal)
    4. Generate and create CalendarEvent records
    """
    from apps.garden.models import GardenItem
    from apps.events.models import CalendarEvent
    from .service import GardenLLMService

    try:
        item = GardenItem.objects.get(pk=item_id)
    except GardenItem.DoesNotExist:
        logger.error(f"GardenItem {item_id} not found")
        return

    service = GardenLLMService()

    # Generate description and cares
    result = service.generate_item_description(item.name, item.type)
    if result['description'] or result['cares']:
        GardenItem.objects.filter(pk=item_id).update(
            description=result['description'],
            cares=result['cares'],
        )
        item.refresh_from_db()
        logger.info(f"Updated description/cares for {item.name}")

    # Generate care schedule — delete only AI-generated events, preserve manual ones
    CalendarEvent.objects.filter(item=item, is_manual=False).delete()

    events_data = service.generate_care_schedule(item)
    today = date.today()
    created_count = 0

    for event_data in events_data:
        try:
            days = int(event_data.get('days_from_now', 1))
            event_date = today + timedelta(days=days)
            recurrence = event_data.get('recurrence', 'once')
            event_type = event_data.get('event_type', 'other')

            # Validate choices
            valid_recurrences = ['once', 'weekly', 'monthly', 'yearly']
            valid_event_types = ['watering', 'fertilizing', 'pruning', 'other']
            if recurrence not in valid_recurrences:
                recurrence = 'once'
            if event_type not in valid_event_types:
                event_type = 'other'

            new_event = CalendarEvent.objects.create(
                item=item,
                title=event_data.get('title', f'Care for {item.name}'),
                description=event_data.get('description', ''),
                date=event_date,
                recurrence=recurrence,
                event_type=event_type,
            )
            created_count += 1
            if recurrence != 'once':
                from apps.events.scheduler import generate_recurring_events
                generate_recurring_events(new_event)
        except Exception as e:
            logger.error(f"Failed to create event: {e}")

    logger.info(f"Created {created_count} care events for {item.name}")
    return created_count
