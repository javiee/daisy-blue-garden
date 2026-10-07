import json
import logging
import re
from .providers import get_llm_provider, VisionNotSupportedError
from .prompts import (
    CARE_DESCRIPTION_PROMPT,
    CARE_SCHEDULE_PROMPT,
    PLANT_IDENTIFICATION_PROMPT,
    build_system_prompt,
)

from apps.garden.models import GardenItem

# Single source of truth: derive from the GardenItem choices so the LLM
# response validation never drifts from the model's allowed types.
VALID_ITEM_TYPES = tuple(key for key, _ in GardenItem.TYPE_CHOICES)

logger = logging.getLogger(__name__)


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences that LLMs often wrap JSON in."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    match = re.match(r'^```(?:json)?\s*([\s\S]*?)\s*```$', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _parse_json_response(response: str, context: str) -> tuple[any, str | None]:
    """
    Parse a JSON response from the LLM. Returns (parsed, error_message).
    Handles empty responses and markdown-wrapped JSON.
    """
    if not response or not response.strip():
        return None, f"Empty response from LLM for {context}"

    cleaned = _strip_markdown_fences(response)

    if not cleaned:
        return None, f"Response was only whitespace/markdown for {context}"

    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        # Log the first 500 chars of the raw response for debugging
        preview = response[:500].replace('\n', '\\n')
        return None, f"JSON parse error for {context}: {e} | Raw response: {preview}"


class GardenLLMService:
    def __init__(self, language: str = 'en', gardener_prompt: str = ''):
        self.provider = get_llm_provider()
        self.language = language
        self.system_prompt = build_system_prompt(language, gardener_prompt)

    def generate_item_description(self, item_name: str, item_type: str) -> dict:
        """Returns {'description': str, 'cares': str}"""
        prompt = CARE_DESCRIPTION_PROMPT.format(
            item_name=item_name,
            item_type=item_type,
        )
        try:
            response = self.provider.generate(prompt, system=self.system_prompt)
            logger.info(f"LLM description response for {item_name}: {response}")
            data, error = _parse_json_response(response, f"description of {item_name}")
            if error:
                logger.error(f"LLM description generation failed: {error}")
                return {'description': '', 'cares': ''}
            return {
                'description': data.get('description', ''),
                'cares': data.get('cares', ''),
            }
        except Exception as e:
            logger.error(f"LLM description generation failed for {item_name}: {e}")
            return {'description': '', 'cares': ''}

    def identify_plant(self, image_path: str) -> dict:
        """
        Send a photo to the vision LLM and get back plant data.
        Returns {'name', 'type', 'description', 'cares', 'error'}.
        On success error is ''; on failure name/description/cares are '' and
        error holds a readable message.
        """
        empty = {'name': '', 'type': '', 'description': '', 'cares': '', 'error': ''}
        try:
            response = self.provider.generate(
                PLANT_IDENTIFICATION_PROMPT,
                system=self.system_prompt,
                image_path=image_path,
            )
        except VisionNotSupportedError as e:
            logger.error(f"LLM provider cannot process images: {e}")
            return {**empty, 'error': str(e)}
        except Exception as e:
            logger.error(f"LLM plant identification failed: {e}")
            return {**empty, 'error': f'Identification failed: {e}'}

        data, error = _parse_json_response(response, 'plant identification')
        if error:
            logger.error(f"LLM identification parse failed: {error}")
            return {**empty, 'error': 'Could not read an answer from the plant expert.'}
        if not isinstance(data, dict):
            logger.error(f"LLM identification returned non-object: {type(data).__name__}")
            return {**empty, 'error': 'Could not read an answer from the plant expert.'}

        item_type = str(data.get('type', '')).strip().lower()
        if item_type not in VALID_ITEM_TYPES:
            item_type = 'plant'

        return {
            'name': str(data.get('name', '')).strip(),
            'type': item_type,
            'description': str(data.get('description', '')).strip(),
            'cares': str(data.get('cares', '')).strip(),
            'error': '',
        }

    def generate_care_schedule(self, item) -> list[dict]:
        """Returns list of event dicts to create as CalendarEvents."""
        # If description/cares are still empty (LLM hasn't run yet),
        # generate them inline rather than sending an empty prompt.
        description = item.description or f"A {item.type} called {item.name}"
        cares = item.cares or "Standard plant care applies."

        prompt = CARE_SCHEDULE_PROMPT.format(
            item_name=item.name,
            item_type=item.type,
            description=description,
            cares=cares,
        )
        try:
            response = self.provider.generate(prompt, system=self.system_prompt)
            logger.info(f"LLM description response for {item.name}: {response}")
            events, error = _parse_json_response(response, f"care schedule for {item.name}")
            if error:
                logger.error(f"LLM schedule generation failed for {item.name}: {error}")
                return []
            if not isinstance(events, list):
                logger.error(
                    f"LLM schedule for {item.name} returned non-list: {type(events).__name__}"
                )
                return []
            return events
        except Exception as e:
            logger.error(f"LLM schedule generation failed for {item.name}: {e}")
            return []
