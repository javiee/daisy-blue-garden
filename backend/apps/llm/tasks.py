import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

def identify_plant_async(identification_id: int):
    """
    1. Fetch PlantIdentification (with uploaded photo)
    2. Send the photo to the vision LLM
    3. Update the record: complete + fields, or failed + readable error
    """
    from apps.llm.models import PlantIdentification
    from apps.core.models import AppSetting
    from .service import GardenLLMService

    try:
        record = PlantIdentification.objects.get(pk=identification_id)
    except PlantIdentification.DoesNotExist:
        logger.error(f"PlantIdentification {identification_id} not found")
        return None

    if not record.photo:
        record.status = 'failed'
        record.error = 'No photo was uploaded.'
        record.save(update_fields=['status', 'error', 'updated_at'])
        return 'failed'

    setting = AppSetting.current()
    service = GardenLLMService(
        language=setting.language,
        gardener_prompt=setting.gardener_prompt,
    )
    result = service.identify_plant(record.photo.path)

    if result['error']:
        record.status = 'failed'
        record.error = result['error']
    elif not result['name']:
        record.status = 'failed'
        record.error = 'Could not identify a plant in this photo. Try a clearer, closer shot.'
    else:
        record.status = 'complete'
        record.name = result['name']
        record.type = result['type']
        record.description = result['description']
        record.cares = result['cares']
    record.save(update_fields=['status', 'error', 'name', 'type', 'description', 'cares', 'updated_at'])
    logger.info(f"Plant identification {identification_id}: {record.status}")
    return record.status


def generate_item_care_async(item_id: int):
    """
    1. Fetch GardenItem
    2. Call LLM to generate description and cares
    3. Update item (without re-triggering signal)
    4. Generate and create CalendarEvent records
    """
    from apps.garden.models import GardenItem
    from apps.events.models import CalendarEvent
    from apps.core.models import AppSetting
    from .service import GardenLLMService

    try:
        item = GardenItem.objects.get(pk=item_id)
    except GardenItem.DoesNotExist:
        logger.error(f"GardenItem {item_id} not found")
        return

    setting = AppSetting.current()
    service = GardenLLMService(
        language=setting.language,
        gardener_prompt=setting.gardener_prompt,
    )

    # Generate description and cares — unless both are already populated
    # (e.g. from photo identification). Never clobber those; the care
    # schedule below is still generated from the existing text.
    if not (item.description and item.cares):
        result = service.generate_item_description(item.name, item.type)
        if result['description'] or result['cares']:
            item.description = result['description']
            item.cares = result['cares']
            # Model.save() with explicit updated_at: QuerySet.update() and
            # update_fields without auto_now fields do not bump updated_at
            item.save(update_fields=['description', 'cares', 'updated_at'])
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

            raw_end_date = event_data.get('end_date')
            end_date = None
            if raw_end_date:
                try:
                    from datetime import date as date_cls
                    end_date = date_cls.fromisoformat(str(raw_end_date))
                except (ValueError, TypeError):
                    end_date = None

            new_event = CalendarEvent.objects.create(
                item=item,
                title=event_data.get('title', f'Care for {item.name}'),
                description=event_data.get('description', ''),
                date=event_date,
                end_date=end_date,
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
