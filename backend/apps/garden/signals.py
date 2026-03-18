from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GardenItem


@receiver(post_save, sender=GardenItem)
def on_garden_item_created(sender, instance, created, **kwargs):
    """Trigger async LLM care generation when a new garden item is created."""
    if created:
        try:
            from apps.llm.tasks import generate_item_care_async
            generate_item_care_async.delay(instance.pk)
        except Exception:
            # Don't let signal errors crash item creation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to trigger LLM care generation for item {instance.pk}")
