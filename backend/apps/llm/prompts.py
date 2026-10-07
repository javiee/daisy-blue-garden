CARE_SYSTEM_PROMPT = """You are a professional botanist and gardening expert.
Provide accurate, practical gardening advice tailored to the specific plant or tree.
Always be specific, actionable, and use metric measurements where applicable."""

LANGUAGE_INSTRUCTIONS = {
    'en': "Write all generated text (descriptions, care guides, event titles and instructions) in English.",
    'es': "Write all generated text (descriptions, care guides, event titles and instructions) in Spanish (español).",
}


def build_system_prompt(language: str, gardener_prompt: str = '') -> str:
    persona = gardener_prompt.strip() or CARE_SYSTEM_PROMPT
    return persona + "\n\n" + LANGUAGE_INSTRUCTIONS.get(
        language, LANGUAGE_INSTRUCTIONS['en']
    )

CARE_DESCRIPTION_PROMPT = """Provide a description and basic care guide for a {item_type} called "{item_name}".

Return your response in the following JSON format:
{{
  "description": "A 2-3 sentence description of the plant/tree including its characteristics and origin.",
  "cares": "A concise care guide covering: watering frequency, sunlight needs, soil type, temperature range, and any special requirements."
}}

Return only valid JSON, no additional text."""

PLANT_IDENTIFICATION_PROMPT = """Look carefully at the attached photo and identify the plant or tree in it.

If you can identify it, give its common name. If you are not sure, give your best guess.

Return your response in the following JSON format:
{{
  "name": "The common name of the plant or tree.",
  "type": "One of: plant, tree, shrub, other.",
  "description": "A 2-3 sentence description of the plant/tree including its characteristics and origin.",
  "cares": "A concise care guide covering: watering frequency, sunlight needs, soil type, temperature range, and any special requirements."
}}

If the photo does not clearly show a plant, still return valid JSON with your best guess for name (or an empty string if nothing is visible) and brief description/cares.

Return only valid JSON, no additional text."""

CARE_SCHEDULE_PROMPT = """Based on the following plant information, create a care schedule with actionable events.

Plant: {item_name}
Type: {item_type}
Description: {description}
Care guide: {cares}

Return a JSON array of care events. Each event should have:
- title: short action title (e.g., "Water {item_name}")
- description: specific instructions
- event_type: one of "watering", "fertilizing", "pruning", "other"
- recurrence: one of "once", "weekly", "monthly", "yearly"
- days_from_now: when to start this task (integer, 1-30)
- end_date: optional ISO date (YYYY-MM-DD) when this recurring event should stop; omit or set to null if it should repeat indefinitely

Example response:
[
  {{
    "title": "Water {item_name}",
    "description": "Water thoroughly at the base, avoiding leaves. Allow soil to dry slightly between waterings.",
    "event_type": "watering",
    "recurrence": "weekly",
    "days_from_now": 1,
    "end_date": null
  }},
  {{
    "title": "Fertilize {item_name}",
    "description": "Apply balanced NPK fertilizer (10-10-10) diluted to half strength.",
    "event_type": "fertilizing",
    "recurrence": "monthly",
    "days_from_now": 7,
    "end_date": "2026-09-30" 
  }}
]

Return only valid JSON array, no additional text. Include 3-6 relevant events."""
