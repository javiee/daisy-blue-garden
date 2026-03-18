import json
import logging
from .providers import get_llm_provider
from .prompts import (
    CARE_SYSTEM_PROMPT,
    CARE_DESCRIPTION_PROMPT,
    CARE_SCHEDULE_PROMPT,
)

logger = logging.getLogger(__name__)


class GardenLLMService:
    def __init__(self):
        self.provider = get_llm_provider()

    def generate_item_description(self, item_name: str, item_type: str) -> dict:
        """
        Returns {'description': str, 'cares': str}
        """
        prompt = CARE_DESCRIPTION_PROMPT.format(
            item_name=item_name,
            item_type=item_type,
        )
        try:
            response = self.provider.generate(prompt, system=CARE_SYSTEM_PROMPT)
            data = json.loads(response.strip())
            return {
                'description': data.get('description', ''),
                'cares': data.get('cares', ''),
            }
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"LLM description generation failed for {item_name}: {e}")
            return {'description': '', 'cares': ''}

    def generate_care_schedule(self, item) -> list[dict]:
        """
        Returns list of event dicts to create as CalendarEvents.
        Each dict: {title, description, event_type, recurrence, days_from_now}
        """
        prompt = CARE_SCHEDULE_PROMPT.format(
            item_name=item.name,
            item_type=item.type,
            description=item.description,
            cares=item.cares,
        )
        try:
            response = self.provider.generate(prompt, system=CARE_SYSTEM_PROMPT)
            events = json.loads(response.strip())
            if not isinstance(events, list):
                return []
            return events
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"LLM schedule generation failed for {item.name}: {e}")
            return []
