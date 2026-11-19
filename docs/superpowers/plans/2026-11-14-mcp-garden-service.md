# MCP Garden Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An MCP streamable-HTTP service on port 8001 that lets external AI clients read the garden (plants, AI care guides, care calendar) and add care events.

**Architecture:** A new top-level package `backend/mcp_service/` holds plain Django ORM tool functions (`tools.py`) plus a thin `MCPServer` wrapper (`app.py`) run by uvicorn as its own docker-compose service, reusing the backend image (WSGI gunicorn cannot host the ASGI-only MCP transport). The MCP Python SDK is **v2** (`MCPServer`); the v1 `FastMCP` no longer exists.

**Tech Stack:** Python 3.12, Django (existing), `mcp>=2,<3` (v2.3.0 verified), uvicorn, Starlette (ships with mcp), Django TestCase.

**Spec:** `docs/superpowers/specs/2026-11-14-mcp-garden-service-design.md`

## Global Constraints

- MCP SDK **v2 only**: `from mcp.server import MCPServer` and `from mcp.server.transport_security import TransportSecuritySettings`. Never import `mcp.server.fastmcp` (removed in v2).
- The new package must **not** be named `mcp` — it would shadow the installed SDK inside the container (WORKDIR `/app` is on `sys.path`). It is `mcp_service`.
- Tool functions return plain JSON-serializable dicts. On failure **return `{"error": "<message>"}` — never raise**: the v2 SDK replaces a raised exception's message with a generic `Error executing tool <name>` (verified against 2.3.0).
- Caps: `list_garden_items` returns at most **50** items, `list_care_events` at most **100** events; both include `"count"` (total matches) and `"truncated"` (bool).
- Dates are ISO `YYYY-MM-DD` strings. `list_care_events` default window: today through today+180 days, inclusive.
- `photo_url` is `None` when there is no photo, else `f"{settings.PUBLIC_BASE_URL}/media/{item.photo.name}"`. `PUBLIC_BASE_URL` is a new setting (env var, default `http://localhost:8000`); the server env value is `http://192.168.10.65:8000`.
- Events created via `add_care_event` set `is_manual=True` (user-initiated; LLM care regeneration deletes `is_manual=False` events — `backend/apps/llm/tasks.py:91`).
- Ordering: garden items `-created_at` (model Meta), events `date` (model Meta).
- **Test environment — this machine is NixOS with no system python/docker.** One-time bootstrap if `/tmp/garden-venv/bin/python` does not exist:
  ```bash
  PY=$(nix eval --raw nixpkgs#python312)
  PATH="$PY/bin:$PATH" python3 -m venv /tmp/garden-venv
  grep -v "^mysqlclient" backend/requirements.txt > /tmp/reqs-no-mysql.txt
  /tmp/garden-venv/bin/pip install -r /tmp/reqs-no-mysql.txt
  ```
  `mysqlclient` is excluded on purpose: local tests run on sqlite (Django falls back when `DATABASE_URL` is unset) and mysqlclient does not build on this machine.
- Test commands:
  - New code: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
  - Full suite: `cd backend && /tmp/garden-venv/bin/python manage.py test` (124 tests, ~5s)
- Commits: conventional subjects matching existing history (`feat: ...`).

## Review Focus

1. **LAN client connects to `http://192.168.10.65:8001/mcp`** — SDK transport security defaults to localhost-only; every request is `421 Misdirected Request` until `192.168.10.65:*` is in `allowed_hosts`. Pinned by Task 4's allowlist test and Task 5's live check.
2. **`add_care_event` with an invalid choice, bad date, or unknown item** — must return an error dict and create **no** DB row. Pinned by Task 3 tests.
3. **`get_garden_item` with a nonexistent id** — `{"error": "Garden item <id> not found"}`, not an exception. Pinned by Task 2 test.
4. **`list_care_events` with no args** — only events dated today or later, up to +180 days; past events excluded. Pinned by Task 3 test.
5. **Item without a photo** — `photo_url` is `None` (no crash, no `"None"` string). Pinned by Task 2 test.

---

### Task 1: Scaffolding, dependencies, PUBLIC_BASE_URL setting

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/config/settings/base.py` (after the Telegram block, ~line 111)
- Create: `backend/mcp_service/__init__.py` (empty)
- Create: `backend/mcp_service/tests/__init__.py` (empty)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: importable `mcp_service` package; `settings.PUBLIC_BASE_URL` (str); `mcp` v2 + uvicorn in the test venv.

- [ ] **Step 1: Add dependencies**

Append to `backend/requirements.txt`:

```
mcp>=2,<3
uvicorn>=0.30
```

- [ ] **Step 2: Add the setting**

In `backend/config/settings/base.py`, after the Telegram block:

```python
# Public base URL of this backend, used by the MCP service to build absolute
# photo URLs (the API returns them absolute from the request Host; MCP has no request).
PUBLIC_BASE_URL = env('PUBLIC_BASE_URL', default='http://localhost:8000')
```

- [ ] **Step 3: Create the package**

Create both empty `__init__.py` files.

- [ ] **Step 4: Install into the test venv**

```bash
/tmp/garden-venv/bin/pip install -q "mcp>=2,<3" uvicorn
```
(Bootstrap the venv first per Global Constraints if it is missing.)

- [ ] **Step 5: Verify the SDK API surface**

Run: `/tmp/garden-venv/bin/python -c "from mcp.server import MCPServer; from mcp.server.transport_security import TransportSecuritySettings; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Run the full suite (no regressions)**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test`
Expected: `Ran 124 tests ... OK`

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/config/settings/base.py backend/mcp_service docs/superpowers
git commit -m "feat: scaffold mcp_service package with mcp v2 + uvicorn deps and PUBLIC_BASE_URL"
```
(This also commits the untracked spec and this plan under `docs/superpowers/`.)

---

### Task 2: tools.py — list_garden_items and get_garden_item

**Files:**
- Create: `backend/mcp_service/tools.py`
- Test: `backend/mcp_service/tests/test_tools.py`

**Interfaces:**
- Consumes: `apps.garden.models.GardenItem`, `apps.events.models.CalendarEvent`, `settings.PUBLIC_BASE_URL` (Task 1).
- Produces (Task 4 wraps these verbatim):
  ```python
  def list_garden_items(type: str | None = None, search: str | None = None) -> dict
  def get_garden_item(item_id: int) -> dict
  ```
  - `list_garden_items` → `{"count": int, "truncated": bool, "items": [item_dict, ...]}` where
    `item_dict = {"id": int, "name": str, "type": str, "description": str, "cares": str, "photo_url": str | None, "event_count": int}`.
    `search` is a case-insensitive substring match on name, type, or description (same fields as the DRF viewset). Cap 50.
  - `get_garden_item` → `{"id", "name", "type", "description", "cares", "photo_url", "created_at", "updated_at", "events": [event_dict, ...]}` where
    `event_dict = {"id", "title", "description", "date", "recurrence", "event_type", "is_manual"}`;
    `created_at`/`updated_at` are ISO dates (`.date().isoformat()`), event `date` an ISO string;
    unknown id → `{"error": f"Garden item {item_id} not found"}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/mcp_service/tests/test_tools.py`:

```python
import io
import shutil
import tempfile
from datetime import date

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from PIL import Image

from apps.events.models import CalendarEvent
from apps.garden.models import GardenItem
from mcp_service import tools


def make_tiny_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'green').save(buf, 'JPEG')
    return buf.getvalue()


class ToolTestBase(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='mcp-test-media-')
        self._media_ctx = override_settings(MEDIA_ROOT=self.media_root)
        self._media_ctx.__enter__()
        self.rose = GardenItem.objects.create(
            name='Rose', type='plant', description='A rose.',
            cares='Water twice a week. Prefers full sun, well-drained soil.')
        self.oak = GardenItem.objects.create(name='Oak', type='tree')
        self.oak.photo.save('oak.jpg', ContentFile(make_tiny_jpeg()), save=True)
        CalendarEvent.objects.create(
            item=self.rose, title='Water Rose', date=date.today(),
            recurrence='weekly', event_type='watering')

    def tearDown(self):
        self._media_ctx.__exit__(None, None, None)
        shutil.rmtree(self.media_root, ignore_errors=True)


class ListGardenItemsTest(ToolTestBase):
    def test_returns_all_with_fields(self):
        result = tools.list_garden_items()
        self.assertEqual(result['count'], 2)
        self.assertFalse(result['truncated'])
        self.assertEqual(len(result['items']), 2)
        rose = next(i for i in result['items'] if i['name'] == 'Rose')
        self.assertEqual(
            set(rose), {'id', 'name', 'type', 'description', 'cares', 'photo_url', 'event_count'})
        self.assertEqual(rose['photo_url'], None)
        self.assertEqual(rose['event_count'], 1)

    def test_photo_url_is_absolute(self):
        result = tools.list_garden_items()
        oak = next(i for i in result['items'] if i['name'] == 'Oak')
        self.assertEqual(oak['photo_url'], 'http://localhost:8000/media/garden/oak.jpg')

    def test_filters_by_type(self):
        result = tools.list_garden_items(type='tree')
        self.assertEqual([i['name'] for i in result['items']], ['Oak'])

    def test_search_matches_name_and_description(self):
        self.assertEqual(len(tools.list_garden_items(search='rose')['items']), 1)
        self.assertEqual(len(tools.list_garden_items(search='full sun')['items']), 1)
        self.assertEqual(tools.list_garden_items(search='zzz')['count'], 0)

    def test_truncates_over_50(self):
        for n in range(49):
            GardenItem.objects.create(name=f'Filler {n}', type='plant')
        result = tools.list_garden_items()
        self.assertEqual(result['count'], 51)
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['items']), 50)


class GetGardenItemTest(ToolTestBase):
    def test_found_includes_events(self):
        result = tools.get_garden_item(self.rose.pk)
        self.assertEqual(result['name'], 'Rose')
        self.assertEqual(result['events'][0]['title'], 'Water Rose')
        self.assertEqual(result['events'][0]['event_type'], 'watering')
        self.assertRegex(result['created_at'], r'^\d{4}-\d{2}-\d{2}$')  # date-only ISO

    def test_not_found_returns_error_dict(self):
        result = tools.get_garden_item(9999)
        self.assertEqual(result, {'error': 'Garden item 9999 not found'})
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_service.tools'`

- [ ] **Step 3: Implement both functions in `backend/mcp_service/tools.py`**

Shared helper `_photo_url(item) -> str | None` (None when `not item.photo`, else `f"{settings.PUBLIC_BASE_URL}/media/{item.photo.name}"`) and `_event_dict(event)` for the event shape above. `list_garden_items` filters `GardenItem.objects` with `type` (exact) and `search` via `Q(name__icontains=...) | Q(type__icontains=...) | Q(description__icontains=...)`, annotates `event_count=Count('events')`, takes `.all()[:50]`, and computes `count` from the untruncated queryset. `get_garden_item` does `GardenItem.objects.filter(pk=item_id).first()` and returns the error dict when None.

- [ ] **Step 4: Run to verify they pass**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/mcp_service/tools.py backend/mcp_service/tests/test_tools.py
git commit -m "feat: mcp tools list_garden_items and get_garden_item"
```

---

### Task 3: tools.py — list_care_events and add_care_event

**Files:**
- Modify: `backend/mcp_service/tools.py`
- Test: `backend/mcp_service/tests/test_tools.py` (append)

**Interfaces:**
- Consumes: `CalendarEvent`, `GardenItem` (existing models); helpers from Task 2.
- Produces (Task 4 wraps these verbatim):
  ```python
  def list_care_events(item_id: int | None = None, event_type: str | None = None,
                       from_date: str | None = None, to_date: str | None = None) -> dict
  def add_care_event(item_id: int, title: str, date: str, event_type: str,
                     recurrence: str = 'once', description: str = '') -> dict
  ```
  - `list_care_events` → `{"count", "truncated", "events": [{"id", "item_id", "item_name", "title", "description", "date", "recurrence", "event_type", "is_manual"}, ...]}` sorted by `date`, cap 100.
    Default window today..today+180 days when both date args are omitted; explicit `from_date`/`to_date` are inclusive bounds (either alone may be given).
    Errors (dicts, checked in this order): unparseable date → `{"error": "Invalid date '<v>': use YYYY-MM-DD"}`; `item_id` not found → `{"error": f"Garden item {item_id} not found"}`; `event_type` not in `CalendarEvent.EVENT_TYPE_CHOICES` → `{"error": f"Invalid event_type '<v>'. Valid: watering, fertilizing, pruning, other"}`.
  - `add_care_event` → on success the created event as `{"status": "created"}` merged with the event shape from `list_care_events` (plus the event's `id`); errors in this order: unknown item, invalid date, empty/blank `title`, invalid `event_type`, invalid `recurrence` (`once, weekly, monthly, yearly`). Creates with `is_manual=True`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/mcp_service/tests/test_tools.py` (import `timedelta` at top with the other stdlib imports):

```python
class ListCareEventsTest(ToolTestBase):
    def _event(self, **kwargs):
        defaults = dict(item=self.rose, title='t', date=date.today(),
                        recurrence='once', event_type='watering')
        defaults.update(kwargs)
        return CalendarEvent.objects.create(**defaults)

    def test_default_window_excludes_past(self):
        self._event(date=date.today() - timedelta(days=1))
        self._event(date=date.today())
        self._event(date=date.today() + timedelta(days=180))
        self._event(date=date.today() + timedelta(days=181))
        result = tools.list_care_events()
        dates = [e['date'] for e in result['events']]
        # 3 in window: 'Water Rose' (today, from setUp) + today + +180; -1 and +181 excluded
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates, sorted(dates))

    def test_explicit_range_is_inclusive(self):
        # Oak has no setUp events, so the count is date-independent.
        self._event(item=self.oak, date=date(2026, 11, 1))
        self._event(item=self.oak, date=date(2026, 11, 14))
        self._event(item=self.oak, date=date(2026, 11, 15))
        result = tools.list_care_events(
            item_id=self.oak.pk, from_date='2026-11-01', to_date='2026-11-14')
        self.assertEqual(result['count'], 2)

    def test_filters_by_item_and_event_type(self):
        self._event(item=self.oak, event_type='fertilizing')
        self._event(event_type='pruning')
        result = tools.list_care_events(item_id=self.rose.pk, event_type='watering')
        self.assertEqual([e['title'] for e in result['events']], ['Water Rose'])

    def test_events_include_item_name(self):
        result = tools.list_care_events()
        self.assertEqual(result['events'][0]['item_name'], 'Rose')

    def test_bad_date_returns_error(self):
        self.assertEqual(
            tools.list_care_events(from_date='14/11/2026'),
            {'error': "Invalid date '14/11/2026': use YYYY-MM-DD"})

    def test_unknown_item_returns_error(self):
        self.assertEqual(
            tools.list_care_events(item_id=9999),
            {'error': 'Garden item 9999 not found'})

    def test_truncates_over_100(self):
        for n in range(101):
            self._event(date=date.today() + timedelta(days=n), title=f'e{n}')
        result = tools.list_care_events()
        self.assertEqual(result['count'], 102)  # 101 new + 'Water Rose'
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['events']), 100)


class AddCareEventTest(ToolTestBase):
    def test_creates_event(self):
        result = tools.add_care_event(
            self.rose.pk, 'Deep Water', '2026-12-01', 'watering',
            recurrence='monthly', description='Soak the root zone.')
        self.assertEqual(result['status'], 'created')
        event = CalendarEvent.objects.get(pk=result['id'])
        self.assertEqual(event.title, 'Deep Water')
        self.assertEqual(str(event.date), '2026-12-01')
        self.assertEqual(event.recurrence, 'monthly')
        self.assertTrue(event.is_manual)

    def test_unknown_item_error(self):
        self.assertEqual(
            tools.add_care_event(9999, 't', '2026-12-01', 'watering'),
            {'error': 'Garden item 9999 not found'})

    def test_invalid_date_error(self):
        result = tools.add_care_event(self.rose.pk, 't', 'dec 1', 'watering')
        self.assertEqual(result, {'error': "Invalid date 'dec 1': use YYYY-MM-DD"})

    def test_blank_title_error(self):
        result = tools.add_care_event(self.rose.pk, '   ', '2026-12-01', 'watering')
        self.assertEqual(result, {'error': 'Title must not be blank'})

    def test_invalid_event_type_error(self):
        result = tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'weeding')
        self.assertEqual(
            result,
            {'error': "Invalid event_type 'weeding'. Valid: watering, fertilizing, pruning, other"})

    def test_invalid_recurrence_error(self):
        result = tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'watering', recurrence='daily')
        self.assertEqual(
            result, {'error': "Invalid recurrence 'daily'. Valid: once, weekly, monthly, yearly"})

    def test_no_rows_created_on_errors(self):
        for call in (
            lambda: tools.add_care_event(9999, 't', '2026-12-01', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, 't', 'bad', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, '', '2026-12-01', 'watering'),
            lambda: tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'weeding'),
            lambda: tools.add_care_event(self.rose.pk, 't', '2026-12-01', 'watering', recurrence='daily'),
        ):
            call()
        self.assertEqual(CalendarEvent.objects.count(), 1)  # only 'Water Rose' from setUp
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
Expected: FAIL — `AttributeError: module 'mcp_service.tools' has no attribute 'list_care_events'`

- [ ] **Step 3: Implement both functions in `backend/mcp_service/tools.py`**

Parse dates with `datetime.strptime(value, '%Y-%m-%d').date()` inside `try/except ValueError`. Validate `event_type`/`recurrence` against the model's `*_CHOICES` (the error strings in the tests are exact copy). In `add_care_event`, run all validations before any write, then `CalendarEvent.objects.create(..., is_manual=True)`. `list_care_events` joins `item` for `item_name`, and `count` comes from the untruncated queryset.

- [ ] **Step 4: Run to verify they pass**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
Expected: PASS (21 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/mcp_service/tools.py backend/mcp_service/tests/test_tools.py
git commit -m "feat: mcp tools list_care_events and add_care_event"
```

---

### Task 4: app.py — MCPServer wiring + compose service

**Files:**
- Create: `backend/mcp_service/app.py`
- Modify: `docker-compose.deploy.yml`
- Test: `backend/mcp_service/tests/test_server.py`

**Interfaces:**
- Consumes: the four tool functions from Tasks 2–3 (wrapped verbatim).
- Produces: ASGI `mcp_service.app:app` on port 8001; compose service `mcp`.

- [ ] **Step 1: Write the failing test**

Create `backend/mcp_service/tests/test_server.py`:

```python
from django.test import TestCase


class AppModuleTest(TestCase):
    def test_mcp_route_exists(self):
        from mcp_service import app as app_module
        paths = [getattr(route, 'path', None) for route in app_module.app.routes]
        self.assertIn('/mcp', paths)

    def test_lan_host_is_allowed(self):
        # SDK transport security defaults to localhost-only: without this,
        # every LAN request is rejected with 421 Misdirected Request.
        from mcp_service import app as app_module
        self.assertIn('192.168.10.65:*', app_module.security.allowed_hosts)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service.test_server`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_service.app'`

- [ ] **Step 3: Create `backend/mcp_service/app.py`**

Structure: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')` + `django.setup()` at module top (before importing tools), then `MCPServer("DaisyBlue Gardener")`, four `@mcp.tool()` wrappers that call the functions verbatim, then:

```python
security = TransportSecuritySettings(
    allowed_hosts=['localhost:*', '127.0.0.1:*', '192.168.10.65:*'],
)
app = mcp.streamable_http_app(stateless_http=True, transport_security=security)
```

The docstrings are the model-facing API — use exactly:

- `list_garden_items(type, search)`: "List the plants and trees in the garden. Returns each item's name, type (plant/tree/shrub/other), AI-generated description, care guide, photo URL and number of calendar events. Optional type filter (plant, tree, shrub, other) and case-insensitive text search over name, type and description."
- `get_garden_item(item_id)`: "Get full details of one garden item by id: description, care guide, photo URL and its complete care calendar. Use list_garden_items first to find ids."
- `list_care_events(item_id, event_type, from_date, to_date)`: "List care calendar events (watering, fertilizing, pruning, other). Dates are YYYY-MM-DD. Defaults to the next 6 months. Filter by item_id, event_type, and/or an inclusive from_date..to_date range."
- `add_care_event(item_id, title, date, event_type, recurrence, description)`: "Create a care calendar event for a garden item. date is YYYY-MM-DD. event_type: watering, fertilizing, pruning, other. recurrence: once (default), weekly, monthly, yearly. Returns the created event."

- [ ] **Step 4: Run to verify it passes**

Run: `cd backend && /tmp/garden-venv/bin/python manage.py test mcp_service`
Expected: PASS (23 tests)

- [ ] **Step 5: Add the compose service**

In `docker-compose.deploy.yml`, after the `qcluster` service:

```yaml
  mcp:
    build: ./backend
    entrypoint: []
    command: uvicorn mcp_service.app:app --host 0.0.0.0 --port 8001
    ports:
      - "8001:8001"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.dev
    env_file: .env
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

- [ ] **Step 6: Runtime check against local sqlite**

Start the server in the background:
```bash
cd backend && /tmp/garden-venv/bin/uvicorn mcp_service.app:app --port 8001
```
Then run a throwaway SDK client (write to `/tmp/opencode/mcp_check.py`):

```python
import asyncio
from mcp import Client


async def main() -> None:
    async with Client('http://127.0.0.1:8001/mcp') as client:
        names = [t.name for t in (await client.list_tools()).tools]
        print('tools:', names)
        r = await client.call_tool('list_garden_items', {})
        print('list:', r.content[0].text)
        r2 = await client.call_tool('get_garden_item', {'item_id': 999999})
        print('missing item ->', r2.content[0].text)

asyncio.run(main())
```

Run: `/tmp/garden-venv/bin/python /tmp/opencode/mcp_check.py`
Expected: the 4 tool names in that order; `list:` shows valid JSON with `"count"` equal to the number of items (local sqlite, may be 0); `missing item ->` shows `{"error": "Garden item 999999 not found"}`. Then stop the background uvicorn and delete `/tmp/opencode/mcp_check.py`.

- [ ] **Step 7: Commit**

```bash
git add backend/mcp_service/app.py backend/mcp_service/tests/test_server.py docker-compose.deploy.yml
git commit -m "feat: mcp streamable-http service (app.py + compose service on :8001)"
```

---

### Task 5: Server env, docs, deploy, end-to-end verification

**Files:**
- Create: `deploy/env.javi` (recreated from the live server `.env`; it is gitignored and absent on this machine)
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: everything from Tasks 1–4.
- Produces: the service live at `http://192.168.10.65:8001/mcp`.

- [ ] **Step 1: Recreate `deploy/env.javi` and add `PUBLIC_BASE_URL`**

```bash
mkdir -p deploy
ssh javi 'cat ~/www-sites/gardener/.env' > deploy/env.javi
grep -q '^PUBLIC_BASE_URL=' deploy/env.javi || echo 'PUBLIC_BASE_URL=http://192.168.10.65:8000' >> deploy/env.javi
```
Check the result contains the new line and the existing keys (SECRET_KEY, DATABASE_URL, LLM_*, TELEGRAM_*, ALLOWED_HOSTS).

- [ ] **Step 2: Document in `CLAUDE.md`**

Add an "### MCP" section under "## API Documentation" (after Settings), documenting: endpoint `http://192.168.10.65:8001/mcp` (streamable HTTP, stateless); the four tools with one line each (copy the docstrings from Task 4); note that tools return `{"error": "..."}` dicts on failure; `PUBLIC_BASE_URL` env var and its purpose. Add `mcp` (8001) to the Docker deployment services table.

- [ ] **Step 3: Document in `AGENTS.md`**

In the Deployment section, add `+ mcp (MCP streamable-HTTP, :8001)` to the stack bullet. Add two troubleshooting table rows: `MCP client gets 421` → "transport-security allowlist in `backend/mcp_service/app.py` must include the host the client uses; add it and redeploy"; `mcp service not running` → "it only starts when backend is healthy (depends_on); check `docker compose ps`".

- [ ] **Step 4: Deploy**

Run: `./deploy.sh`
Expected: rsync + image build + `docker compose ps` showing `backend`, `qcluster`, `frontend` **and `mcp`** all up; health checks 200/200.

- [ ] **Step 5: End-to-end verification from this machine**

Recreate `/tmp/opencode/mcp_check.py` as in Task 4 step 6 but pointing at the server (`http://192.168.10.65:8001/mcp`), and add one read of the real data:

```python
r3 = await client.call_tool('list_care_events', {})
print('events:', r3.content[0].text[:300])
```

Run: `/tmp/garden-venv/bin/python /tmp/opencode/mcp_check.py`
Expected: 4 tool names; `list:` shows the real garden (count 7 as of writing); a photo `photo_url` value beginning `http://192.168.10.65:8000/media/`; `events:` shows the real upcoming care. No `421` / transport errors. Then delete the check script. (Read-only by design — `add_care_event` is covered by Task 3's tests; do not create rows in the production DB.)

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md AGENTS.md
git commit -m "docs: document mcp service (endpoint, tools, env, troubleshooting)"
```
