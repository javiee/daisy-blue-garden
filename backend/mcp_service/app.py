"""MCP streamable-HTTP server for the garden.

Run: ``uvicorn mcp_service.app:app --host 0.0.0.0 --port 8001``
(docker compose service ``mcp`` in docker-compose.deploy.yml).

Django must be set up before the tool functions (and their models) are
imported, so setup happens at module import time, before uvicorn loads the
ASGI ``app``.
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from mcp_service import tools

mcp = MCPServer("DaisyBlue Gardener")


@mcp.tool()
def list_garden_items(type: str | None = None, search: str | None = None) -> dict:
    """List the plants and trees in the garden. Returns each item's name, type (plant/tree/shrub/other), AI-generated description, care guide, photo URL and number of calendar events. Optional type filter (plant, tree, shrub, other) and case-insensitive text search over name, type and description."""
    return tools.list_garden_items(type=type, search=search)


@mcp.tool()
def get_garden_item(item_id: int) -> dict:
    """Get full details of one garden item by id: description, care guide, photo URL and its complete care calendar. Use list_garden_items first to find ids."""
    return tools.get_garden_item(item_id)


@mcp.tool()
def list_care_events(item_id: int | None = None, event_type: str | None = None,
                     from_date: str | None = None, to_date: str | None = None) -> dict:
    """List care calendar events (watering, fertilizing, pruning, other). Dates are YYYY-MM-DD. Defaults to the next 6 months. Filter by item_id, event_type, and/or an inclusive from_date..to_date range."""
    return tools.list_care_events(item_id=item_id, event_type=event_type,
                                  from_date=from_date, to_date=to_date)


@mcp.tool()
def add_care_event(item_id: int, title: str, date: str, event_type: str,
                   recurrence: str = 'once', description: str = '') -> dict:
    """Create a care calendar event for a garden item. date is YYYY-MM-DD. event_type: watering, fertilizing, pruning, other. recurrence: once (default), weekly, monthly, yearly. Returns the created event."""
    return tools.add_care_event(item_id, title, date, event_type,
                                recurrence=recurrence, description=description)


security = TransportSecuritySettings(
    allowed_hosts=['localhost:*', '127.0.0.1:*', '192.168.10.65:*'],
)
app = mcp.streamable_http_app(stateless_http=True, transport_security=security)
