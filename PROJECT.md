# DaisyBlue Gardener — Project Overview

> An AI-powered garden management application that helps you track plants, get automated care guides, and receive smart reminders via Telegram.

---

## Table of Contents

1. [What Is DaisyBlue Gardener?](#what-is-daisyblue-gardener)
2. [How It Works — The Big Picture](#how-it-works--the-big-picture)
3. [Architecture Overview](#architecture-overview)
4. [Component Deep Dive](#component-deep-dive)
   - [Backend (Django)](#backend-django)
   - [LLM Integration](#llm-integration)
   - [Notification System](#notification-system)
   - [Frontend (Next.js)](#frontend-nextjs)
   - [Task Queue (Celery + Redis)](#task-queue-celery--redis)
5. [Data Flow Walkthrough](#data-flow-walkthrough)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Running Locally](#running-locally)
9. [Running with Docker](#running-with-docker)
10. [Environment Variables Reference](#environment-variables-reference)
11. [Testing](#testing)
12. [CI/CD Pipeline](#cicd-pipeline)
13. [Project File Structure](#project-file-structure)

---

## What Is DaisyBlue Gardener?

DaisyBlue Gardener is a web application for managing your home garden. You add the plants and trees that live in your garden, and the app takes care of the rest:

- **AI-generated care guides** — as soon as you add a plant, an LLM (OpenAI, Anthropic, or a local Ollama model) automatically generates a description and a tailored care guide.
- **Smart calendar** — based on the care guide, the app creates a calendar of recurring actions (water weekly, fertilize monthly, prune in spring, etc.).
- **Telegram reminders** — a Celery scheduler sends you a Telegram message before each care event. You can acknowledge each reminder so you don't get spammed.
- **Beautiful UI** — a Next.js frontend shows your garden as a visual gallery, a calendar view (week and month), and a notification inbox.

---

## How It Works — The Big Picture

```
You add "Red Rose" (type: plant)
        │
        ▼
Django REST API creates GardenItem in MySQL
        │
        ▼  (Django signal fires)
Celery task queued in Redis
        │
        ▼  (background, async)
LLM Provider generates:
  ① description + care guide  → saved to GardenItem
  ② care schedule as JSON     → saved as CalendarEvents
        │
        ▼  (Celery Beat runs on schedule)
Scheduler checks upcoming CalendarEvents
        │
        ▼
Telegram Bot sends you a reminder message
        │
        ▼
You tap "Acknowledge" in the app (or reply /ack_42 on Telegram)
        │
        ▼
Notification marked as acknowledged, suppressed until next occurrence
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser / Mobile                             │
│                      Next.js 15 Frontend                            │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Garden    │  │  Calendar  │  │Notifications│  │  Add Plant  │ │
│  │  Gallery   │  │ Week/Month │  │  + Settings │  │   Form      │ │
│  └────────────┘  └────────────┘  └─────────────┘  └─────────────┘ │
│         TanStack React Query · Tailwind CSS · TypeScript            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP REST (JSON)
                           │ http://localhost:8000/api/v1
┌──────────────────────────▼──────────────────────────────────────────┐
│                    Django 5 + Django REST Framework                 │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌────────────────┐   │
│  │  garden  │  │  events  │  │    llm     │  │ notifications  │   │
│  │  /api/v1 │  │  /api/v1 │  │  /api/v1   │  │   /api/v1      │   │
│  │  /garden │  │  /events │  │  /llm      │  │/notifications  │   │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └───────┬────────┘   │
│       │              │              │                  │            │
│       └──────────────┴──────────────┴──────────────────┘           │
│                              │                                      │
│                         Django ORM                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┼──────────────────┐
              │                │                  │
     ┌────────▼───────┐ ┌──────▼──────┐  ┌───────▼──────────┐
     │   MySQL 8.0    │ │   Redis 7   │  │   LLM Provider   │
     │   (data store) │ │ (task queue)│  │ OpenAI/Anthropic │
     └────────────────┘ └──────┬──────┘  │     /Ollama      │
                               │         └──────────────────┘
                    ┌──────────▼────────┐
                    │  Celery Workers   │
                    │  + Celery Beat    │
                    │  (async tasks &   │
                    │   scheduling)     │
                    └──────────┬────────┘
                               │
                    ┌──────────▼────────┐
                    │   Telegram Bot    │
                    │ (push reminders)  │
                    └───────────────────┘
```

---

## Component Deep Dive

### Backend (Django)

The backend is a Django 5 project with four apps, each owning a specific domain:

#### `apps/garden` — Plant & Tree Management

The core domain. Manages `GardenItem` — the representation of any plant or tree in your garden.

- **Model:** `GardenItem` stores name, type (plant/tree/shrub/other), an AI-generated description, an AI-generated care text, an optional photo, and timestamps.
- **API:** Full CRUD via Django REST Framework. Supports filtering by type (`?type=tree`), text search (`?search=rose`), and ordering.
- **Signal:** When a new `GardenItem` is saved for the first time (`post_save, created=True`), a Django signal fires and enqueues a Celery task to generate the LLM content asynchronously. This means the API response returns immediately — no waiting for the LLM.

```
POST /api/v1/garden/   →   GardenItem created   →   signal fires
                                                       │
                                              Celery task queued
                                              (returns in ~10-30s)
```

#### `apps/events` — Calendar Events

Manages `CalendarEvent` — every actionable care task linked to a `GardenItem`.

- **Model:** Each event has a title, description, date, recurrence type (once/weekly/monthly/yearly), and event type (watering/fertilizing/pruning/other).
- **API:** Supports filtering by week (`?week=2024-W12`) or month (`?month=2024-03`), and by item (`/events/by-item/{id}/`). This powers the calendar UI.
- **Scheduler:** `scheduler.py` contains `generate_recurring_events()` which can expand a recurring event forward up to 6 months, creating individual `CalendarEvent` rows for each occurrence.

#### `apps/llm` — LLM Integration

A provider-agnostic LLM abstraction layer.

- **Providers (`providers.py`):** Abstract base class `BaseLLMProvider` with three implementations:
  - `OpenAIProvider` — uses the `openai` Python SDK
  - `AnthropicProvider` — uses the `anthropic` Python SDK
  - `OllamaProvider` — calls the local Ollama HTTP API (no API key needed)
  - `get_llm_provider()` is a factory function that reads `LLM_PROVIDER` from env and returns the right instance.
- **Prompts (`prompts.py`):** Two structured prompts that ask the LLM to return JSON:
  1. `CARE_DESCRIPTION_PROMPT` → returns `{ description, cares }`
  2. `CARE_SCHEDULE_PROMPT` → returns a list of care events `[{ title, event_type, recurrence, days_from_now, ... }]`
- **Service (`service.py`):** `GardenLLMService` orchestrates calls to the provider and handles JSON parsing and error recovery.
- **Task (`tasks.py`):** `generate_item_care_async` is the Celery task that:
  1. Fetches the `GardenItem`
  2. Calls `generate_item_description()` → updates item in DB
  3. Calls `generate_care_schedule()` → creates `CalendarEvent` rows

#### `apps/notifications` — Telegram Notification System

Manages when and how reminders are sent, and tracks acknowledgements.

- **Models:**
  - `NotificationConfig` — stores the Telegram chat ID, how often to check (daily/weekly/monthly), and how many days before an event to notify.
  - `Notification` — a log of every sent message: status (pending/sent/failed), whether it was acknowledged, and the calculated next occurrence date.
- **Bot (`bot.py`):** Uses `python-telegram-bot` (async) to send formatted Markdown messages to Telegram. The `send_notification_sync()` wrapper makes it usable from synchronous Celery tasks.
- **Tasks (`tasks.py`):**
  - `check_and_send_notifications()` — run on schedule by Celery Beat. For each active `NotificationConfig`, finds upcoming `CalendarEvent`s within `days_before` days, skips ones already notified, and enqueues `send_event_notification` for each.
  - `send_event_notification(event_id, config_id)` — creates a `Notification` record, sends the Telegram message, and updates the status.
- **Acknowledge logic:** When a user acknowledges a notification, the app calculates `next_occurrence_date` based on the event's recurrence (e.g. weekly → today + 7 days). The scheduler skips this event until that date passes.

---

### LLM Integration

The LLM layer is designed to be completely swappable. The active provider is controlled by environment variables:

| Env Var | Description |
|---------|-------------|
| `LLM_PROVIDER` | `openai`, `anthropic`, or `ollama` |
| `LLM_API_KEY` | API key (not needed for Ollama) |
| `LLM_MODEL` | Model name (e.g. `gpt-4o`, `claude-sonnet-4-6`, `llama3.2`) |
| `OLLAMA_BASE_URL` | Base URL for local Ollama (default: `http://localhost:11434`) |

**Prompt design:** Both prompts instruct the LLM to respond only with valid JSON. The service layer parses the JSON and falls back to empty strings/lists on failure — so a broken LLM response never crashes item creation.

**Example LLM output for "Red Rose" (plant):**

```json
// Description prompt output:
{
  "description": "Rosa × hybrida is a classic garden rose prized for its rich red blooms and sweet fragrance. Originating from hybrid breeding programs in the 18th century, it thrives in temperate climates.",
  "cares": "Water 2-3 times per week at the base. Plant in full sun (6+ hours). Use well-draining, slightly acidic soil (pH 6.0-6.5). Feed with rose-specific fertilizer monthly during growing season."
}

// Schedule prompt output:
[
  { "title": "Water Red Rose", "event_type": "watering", "recurrence": "weekly", "days_from_now": 1, "description": "Water deeply at the base, 2-3 litres." },
  { "title": "Fertilize Red Rose", "event_type": "fertilizing", "recurrence": "monthly", "days_from_now": 7, "description": "Apply rose NPK fertilizer at half strength." },
  { "title": "Prune Red Rose", "event_type": "pruning", "recurrence": "yearly", "days_from_now": 90, "description": "Hard prune in early spring before bud break." }
]
```

---

### Notification System

The notification flow is fully asynchronous and non-blocking:

```
Celery Beat (cron)
      │
      ▼
check_and_send_notifications()
      │
      ├── For each NotificationConfig (active=True):
      │     │
      │     ├── Find CalendarEvents due within days_before days
      │     │
      │     ├── Skip if: unacknowledged Notification exists
      │     │            OR acknowledged + next_occurrence_date > today
      │     │
      │     └── Enqueue: send_event_notification(event_id, config_id)
      │
      ▼
send_event_notification()
      │
      ├── Create Notification(status=pending)
      ├── Format Telegram message (Markdown)
      ├── Call Telegram Bot API
      └── Update Notification(status=sent/failed, telegram_message_id)
```

**Telegram message format:**
```
🌸 DaisyBlue Garden Reminder

💧 Water Red Rose

📅 Date: March 25, 2026
🌿 Plant: Red Rose
🏷️ Type: Watering
🔄 Recurrence: Weekly

Water deeply at the base, 2-3 litres.

✅ To acknowledge: /ack_42
```

**Acknowledge flow:**
- User taps "Acknowledge" in the web UI (or sends `/ack_42` via Telegram)
- `POST /api/v1/notifications/42/acknowledge/` is called
- `next_occurrence_date` is computed: weekly → +7 days, monthly → +1 month, yearly → +1 year, once → null
- The scheduler skips this notification until `next_occurrence_date`

---

### Frontend (Next.js)

Built with Next.js 15 App Router, TypeScript, and Tailwind CSS v4.

#### Pages

| Route | Description |
|-------|-------------|
| `/` | Home — garden gallery grid with plant cards |
| `/garden/new` | Add plant form with type selector and photo upload |
| `/garden/[id]` | Plant detail: description, care guide, event list, regenerate button |
| `/calendar` | Week/Month calendar view with navigation |
| `/notifications` | Notification inbox + Telegram settings |

#### State Management

All server state is managed by **TanStack React Query v5**:
- Data is cached and stale-while-revalidate
- Mutations (create, acknowledge) automatically invalidate related queries
- Pending notifications are polled every 60 seconds

#### Key Components

| Component | Purpose |
|-----------|---------|
| `GardenCard` | Plant card with photo, name, type badge, description preview |
| `PlantForm` | Controlled form with Zod validation; shows AI-generating state |
| `WeekView` | 7-column day grid with event pills |
| `MonthView` | Full month grid with colored dot indicators per event type |
| `EventCard` | Single event with type icon, date, recurrence |
| `NotificationItem` | Notification row with acknowledge button |
| `TypeBadge` | Colored badge: 🌿 plant · 🌳 tree · 🌸 shrub · 🍀 other |
| `EventTypeIcon` | Colored pill: 💧 watering · 🌱 fertilizing · ✂️ pruning |
| `Navigation` | Sidebar with pending notification badge counter |

#### API Client (`lib/api.ts`)

A thin typed wrapper around `fetch`. All API calls go through this module, making it easy to swap the base URL or add auth headers later.

```typescript
// Example usage:
const item = await api.garden.get(42)
const events = await api.events.list({ week: '2026-W12' })
await api.notifications.acknowledge(7)
```

---

### Task Queue (Celery + Redis)

Celery handles two types of work:

| Worker | Command | Purpose |
|--------|---------|---------|
| `celery worker` | `celery -A celery worker -l info` | Executes tasks (LLM calls, Telegram sends) |
| `celery beat` | `celery -A celery beat -l info` | Triggers scheduled tasks (notification checks) |

Redis acts as both the **message broker** (task queue) and the **result backend** (task status storage).

**Task flow:**
```
Django API  →  Redis queue  →  Celery worker  →  MySQL / Telegram
```

The Celery Beat schedule for notifications is stored in MySQL via `django-celery-beat`, so it can be updated at runtime without restarting the worker.

---

## Data Flow Walkthrough

### Adding a New Plant

```
1. User fills in "Lavender" + type "plant" on /garden/new
2. Frontend POSTs FormData to POST /api/v1/garden/
3. Django creates GardenItem(name="Lavender", type="plant") in MySQL
4. Django's post_save signal fires → enqueues generate_item_care_async(item_id)
5. API returns 201 { id: 5, name: "Lavender", description: "", ... }
6. Frontend redirects to /garden/5
7. Plant detail page shows "AI is generating a description..."
8. Meanwhile, Celery worker picks up the task:
   a. Calls LLM → gets description + care text
   b. Updates GardenItem in MySQL
   c. Calls LLM again → gets care schedule JSON
   d. Creates CalendarEvent rows in MySQL
9. User refreshes /garden/5 → description and events are now visible
```

### Receiving a Telegram Reminder

```
1. Celery Beat triggers check_and_send_notifications() (e.g. every morning at 9 AM)
2. Task finds CalendarEvents due within 3 days (configurable)
3. For "Water Lavender" on 2026-03-21:
   a. No existing unacknowledged Notification found → proceed
   b. Creates Notification(event=..., status=pending)
   c. Formats Telegram message
   d. Calls Telegram Bot API → message sent
   e. Updates Notification(status=sent, telegram_message_id="12345")
4. User receives Telegram message
5. User taps "Acknowledge" in the web app
6. POST /api/v1/notifications/{id}/acknowledge/
7. Notification.acknowledged = True
8. next_occurrence_date = today + 7 days (weekly recurrence)
9. Next time check_and_send_notifications() runs for this event,
   it sees acknowledged=True + next_occurrence_date in the future → skips
```

---

## Database Schema

```
┌─────────────────────────────────────┐
│           GardenItem                │
├─────────────────────────────────────┤
│ id            INTEGER  PK           │
│ name          VARCHAR(200)          │
│ type          VARCHAR(20)           │
│               plant/tree/shrub/other│
│ description   TEXT                  │
│ cares         TEXT                  │
│ photo         VARCHAR (path)        │
│ created_at    DATETIME              │
│ updated_at    DATETIME              │
└──────────────┬──────────────────────┘
               │ 1:N
               ▼
┌─────────────────────────────────────┐
│          CalendarEvent              │
├─────────────────────────────────────┤
│ id            INTEGER  PK           │
│ item_id       FK → GardenItem       │
│ title         VARCHAR(200)          │
│ description   TEXT                  │
│ date          DATE                  │
│ recurrence    VARCHAR(20)           │
│               once/weekly/monthly/  │
│               yearly                │
│ event_type    VARCHAR(20)           │
│               watering/fertilizing/ │
│               pruning/other         │
│ created_at    DATETIME              │
└──────────────┬──────────────────────┘
               │ 1:N
               ▼
┌─────────────────────────────────────┐
│           Notification              │
├─────────────────────────────────────┤
│ id                 INTEGER  PK      │
│ event_id           FK → CalendarEvent│
│ config_id          FK → NotifConfig │
│ telegram_message_id VARCHAR(100)    │
│ status             VARCHAR(20)      │
│                    pending/sent/    │
│                    failed           │
│ sent_at            DATETIME         │
│ acknowledged       BOOLEAN          │
│ acknowledged_at    DATETIME         │
│ next_occurrence_date DATE           │
│ created_at         DATETIME         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│        NotificationConfig           │
├─────────────────────────────────────┤
│ id              INTEGER  PK         │
│ telegram_chat_id VARCHAR(100)       │
│ frequency        VARCHAR(20)        │
│                  daily/weekly/      │
│                  monthly            │
│ days_before      INTEGER (default 3)│
│ is_active        BOOLEAN            │
│ created_at       DATETIME           │
│ updated_at       DATETIME           │
└─────────────────────────────────────┘
```

---

## API Reference

### Garden Items

```
GET    /api/v1/garden/
  Query: ?type=plant|tree|shrub|other
         ?search=<term>
         ?ordering=name|-created_at
  Returns: { count, next, previous, results: GardenItem[] }

POST   /api/v1/garden/
  Body: multipart/form-data
        name (required), type (required), photo (optional)
  Returns: GardenItem (201)

GET    /api/v1/garden/{id}/        → GardenItem
PUT    /api/v1/garden/{id}/        → GardenItem
DELETE /api/v1/garden/{id}/        → 204
```

### Calendar Events

```
GET    /api/v1/events/
  Query: ?week=2026-W12          (ISO week)
         ?month=2026-03          (YYYY-MM)
         ?item=<id>
         ?event_type=watering|fertilizing|pruning|other
         ?recurrence=once|weekly|monthly|yearly
  Returns: { count, next, previous, results: CalendarEvent[] }

POST   /api/v1/events/            → CalendarEvent (201)
GET    /api/v1/events/{id}/       → CalendarEvent
PUT    /api/v1/events/{id}/       → CalendarEvent
DELETE /api/v1/events/{id}/       → 204

GET    /api/v1/events/by-item/{item_id}/
  Returns: CalendarEvent[]  (all events for one plant)
```

### LLM

```
POST   /api/v1/llm/generate-care/{item_id}/
  Returns: { task_id: string, status: "queued" }
  (Triggers async LLM generation for a plant)

GET    /api/v1/llm/providers/
  Returns: { providers: [...], current: "openai" }
```

### Notifications

```
GET    /api/v1/notifications/
  Returns: { count, next, previous, results: Notification[] }

GET    /api/v1/notifications/pending/
  Returns: Notification[]  (unacknowledged, status=sent)

POST   /api/v1/notifications/{id}/acknowledge/
  Returns: Notification (with acknowledged=true, next_occurrence_date set)

GET    /api/v1/notifications/config/   → NotificationConfig[]
POST   /api/v1/notifications/config/   → NotificationConfig (201)
PUT    /api/v1/notifications/config/{id}/  → NotificationConfig
```

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 22+
- MySQL 8.0 **or** Docker (to run MySQL in a container)
- Redis **or** Docker

### Option A — MySQL + Redis via Docker, app locally

This is the recommended approach for development.

**Step 1 — Start MySQL and Redis only:**
```bash
docker-compose up -d db redis
```

**Step 2 — Backend setup:**
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
```

Edit `.env` — at minimum set:
```bash
DATABASE_URL=mysql://daisyblue:daisyblue_pass@localhost:3306/daisyblue
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=any-random-string-here
LLM_PROVIDER=openai              # or anthropic or ollama
LLM_API_KEY=sk-your-key          # leave blank for ollama
LLM_MODEL=gpt-4o
TELEGRAM_BOT_TOKEN=              # optional for local dev
TELEGRAM_CHAT_ID=                # optional for local dev
```

**Step 3 — Run migrations and start Django:**
```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
# → API available at http://localhost:8000
```

**Step 4 — Start Celery (separate terminal):**
```bash
cd backend
source .venv/bin/activate
celery -A celery worker -l info
```

**Step 5 — Start Celery Beat scheduler (separate terminal):**
```bash
cd backend
source .venv/bin/activate
celery -A celery beat -l info
```

**Step 6 — Frontend setup (separate terminal):**
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
# → UI available at http://localhost:3000
```

### Option B — Ollama (no API key required)

If you don't have an OpenAI/Anthropic key, use a local model:

```bash
# Install Ollama from https://ollama.ai
brew install ollama              # macOS
ollama pull llama3.2             # download model (~2GB)
ollama serve                     # starts on localhost:11434
```

Then in `.env`:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

### Telegram Bot Setup (optional for local dev)

1. Open Telegram and message `@BotFather`
2. Send `/newbot` → follow instructions → copy the token
3. Start a conversation with your new bot
4. Message `@userinfobot` to get your chat ID
5. Set in `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-your-token
   TELEGRAM_CHAT_ID=987654321
   ```
6. Configure via the app's **Notifications → Settings** page

---

## Running with Docker

The entire stack (Django, Next.js, MySQL, Redis, Celery) runs with one command.

**Step 1 — Configure environment:**
```bash
cp .env.example .env
# Edit .env with your LLM API key and Telegram credentials
```

**Step 2 — Start everything:**
```bash
docker-compose up -d
```

**Step 3 — Run migrations:**
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

**Step 4 — Open the app:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- Django Admin: http://localhost:8000/admin

**Services started by docker-compose:**

| Service | Port | Description |
|---------|------|-------------|
| `db` | 3306 | MySQL 8.0 database |
| `redis` | 6379 | Redis (Celery broker) |
| `backend` | 8000 | Django dev server |
| `celery` | — | Celery worker |
| `celery-beat` | — | Celery Beat scheduler |
| `frontend` | 3000 | Next.js app |

**Useful commands:**
```bash
# View logs for all services
docker-compose logs -f

# View logs for one service
docker-compose logs -f backend

# Run Django management commands
docker-compose exec backend python manage.py shell

# Stop everything
docker-compose down

# Stop and remove database volume (full reset)
docker-compose down -v
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes (prod) | insecure default | Django secret key |
| `DEBUG` | No | `True` | Django debug mode |
| `ALLOWED_HOSTS` | Prod only | `*` | Comma-separated allowed hosts |
| `DATABASE_URL` | Yes | SQLite fallback | Full DB connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis for Celery |
| `LLM_PROVIDER` | Yes | `openai` | `openai` / `anthropic` / `ollama` |
| `LLM_API_KEY` | Yes* | — | API key (*not needed for Ollama) |
| `LLM_MODEL` | No | `gpt-4o` | Model identifier |
| `OLLAMA_BASE_URL` | Ollama only | `http://localhost:11434` | Ollama server URL |
| `TELEGRAM_BOT_TOKEN` | For notifications | — | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | For notifications | — | Your Telegram chat ID |
| `CORS_ALLOWED_ORIGINS` | Prod only | — | Comma-separated origins |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://localhost:8000/api/v1` | Backend API base URL |

---

## Testing

### Backend Tests

Tests use Django's built-in `TestCase` + DRF's `APITestCase`. The database is a fresh SQLite instance per test run — no MySQL needed for tests.

```bash
cd backend
source .venv/bin/activate
python manage.py test
```

**Test coverage by app:**

| App | Tests |
|-----|-------|
| `garden` | Model creation, CRUD API, type filtering, search |
| `events` | Model creation, week/month filtering, by-item endpoint |
| `llm` | All three providers (mocked), service JSON parsing, task execution |
| `notifications` | Acknowledge logic, recurrence date calculation, task scheduling, API |

LLM and Telegram API calls are always mocked — tests never make real external requests.

### Frontend Tests

Tests use **Vitest** + **React Testing Library**.

```bash
cd frontend
npm test           # watch mode
npm test -- --run  # single run (CI mode)
```

**Test coverage:**

| Test file | Tests |
|-----------|-------|
| `GardenCard.test.tsx` | Renders name, description, placeholder, link, type badge |
| `TypeBadge.test.tsx` | All four type badges render correctly |
| `NotificationItem.test.tsx` | Renders title, ack button, calls handler, hides button when ack'd |
| `api.test.ts` | API client calls correct endpoints with correct methods |

---

## CI/CD Pipeline

GitHub Actions workflow at `.github/workflows/deploy.yml`:

```
Push to main branch
        │
        ├──────────────────────┐
        ▼                      ▼
test-backend              test-frontend
(Django tests +           (Vitest +
 MySQL service)            Node 22)
        │                      │
        └──────────┬───────────┘
                   ▼
           build-and-push
        (only on main branch)
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  Build backend          Build frontend
  Docker image           Docker image
        │                     │
        ▼                     ▼
  Push to GHCR          Push to GHCR
  (tagged: latest        (tagged: latest
   + sha-{commit})        + sha-{commit})
```

**Image names:**
- `ghcr.io/{owner}/backend:latest`
- `ghcr.io/{owner}/frontend:latest`

Images are cached via GitHub Actions cache to speed up subsequent builds.

---

## Project File Structure

```
daisy-blue-garden/
│
├── CLAUDE.md                    # Architecture & API docs (for AI assistants)
├── PROJECT.md                   # This file
├── docker-compose.yml           # Full stack orchestration
├── .env.example                 # Environment variable template
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline
│
├── backend/
│   ├── manage.py                # Django entry point
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container
│   ├── celery.py                # Celery app definition
│   │
│   ├── config/                  # Django project config
│   │   ├── urls.py              # Root URL routing
│   │   ├── wsgi.py / asgi.py    # WSGI/ASGI entry points
│   │   ├── celery.py            # Celery config re-export
│   │   └── settings/
│   │       ├── base.py          # Shared settings
│   │       ├── dev.py           # Development overrides
│   │       └── prod.py          # Production overrides
│   │
│   └── apps/
│       ├── garden/              # Plant/tree management
│       │   ├── models.py        # GardenItem model
│       │   ├── serializers.py   # DRF serializers
│       │   ├── views.py         # ViewSet (CRUD)
│       │   ├── urls.py          # URL routing
│       │   ├── admin.py         # Django admin
│       │   ├── apps.py          # App config (loads signals)
│       │   ├── signals.py       # post_save → trigger LLM
│       │   └── tests/
│       │       ├── test_models.py
│       │       └── test_views.py
│       │
│       ├── events/              # Calendar events
│       │   ├── models.py        # CalendarEvent model
│       │   ├── serializers.py
│       │   ├── views.py         # Week/month filtering
│       │   ├── urls.py
│       │   ├── admin.py
│       │   ├── apps.py
│       │   ├── scheduler.py     # Recurring event expansion
│       │   └── tests/
│       │       ├── test_models.py
│       │       └── test_views.py
│       │
│       ├── llm/                 # LLM integration
│       │   ├── providers.py     # OpenAI / Anthropic / Ollama
│       │   ├── prompts.py       # Structured prompts
│       │   ├── service.py       # GardenLLMService
│       │   ├── tasks.py         # Celery async task
│       │   ├── views.py         # Manual trigger endpoint
│       │   ├── urls.py
│       │   ├── apps.py
│       │   └── tests/
│       │       ├── test_providers.py
│       │       ├── test_service.py
│       │       └── test_tasks.py
│       │
│       └── notifications/       # Telegram notifications
│           ├── models.py        # NotificationConfig, Notification
│           ├── serializers.py
│           ├── views.py         # List, pending, acknowledge
│           ├── urls.py
│           ├── admin.py
│           ├── apps.py
│           ├── bot.py           # Telegram Bot API integration
│           ├── tasks.py         # check_and_send, send_event
│           └── tests/
│               ├── test_models.py
│               ├── test_tasks.py
│               └── test_views.py
│
└── frontend/
    ├── package.json             # Node dependencies
    ├── next.config.ts           # Next.js configuration
    ├── tsconfig.json            # TypeScript config
    ├── tailwind.config.ts       # Tailwind CSS v4
    ├── postcss.config.mjs       # PostCSS
    ├── vitest.config.ts         # Test runner config
    ├── vitest.setup.ts          # jest-dom matchers
    ├── Dockerfile               # Frontend container (standalone)
    ├── .env.local.example       # Frontend env template
    │
    ├── app/                     # Next.js App Router pages
    │   ├── layout.tsx           # Root layout (header + nav + providers)
    │   ├── globals.css          # Global styles + Tailwind
    │   ├── page.tsx             # / → Garden gallery
    │   ├── garden/
    │   │   ├── [id]/page.tsx    # /garden/:id → Plant detail
    │   │   └── new/page.tsx     # /garden/new → Add plant form
    │   ├── calendar/
    │   │   └── page.tsx         # /calendar → Week/month view
    │   └── notifications/
    │       └── page.tsx         # /notifications → Inbox + settings
    │
    ├── components/              # Reusable UI components
    │   ├── Providers.tsx        # React Query provider wrapper
    │   ├── GardenCard.tsx       # Plant card for gallery
    │   ├── PlantForm.tsx        # Add/edit plant form
    │   ├── EventCard.tsx        # Single event display
    │   ├── EventTypeIcon.tsx    # Colored event type pill
    │   ├── TypeBadge.tsx        # Plant type badge
    │   ├── WeekView.tsx         # 7-day calendar grid
    │   ├── MonthView.tsx        # Full month calendar grid
    │   ├── NotificationItem.tsx # Notification row + ack button
    │   ├── LoadingSkeleton.tsx  # Animated loading placeholder
    │   └── layout/
    │       ├── Header.tsx       # Top navigation bar
    │       └── Navigation.tsx   # Sidebar with notification badge
    │
    ├── lib/                     # Shared utilities
    │   ├── types.ts             # All TypeScript interfaces
    │   ├── api.ts               # Typed fetch API client
    │   ├── hooks.ts             # React Query hooks
    │   └── utils.ts             # Date helpers, cn(), etc.
    │
    └── __tests__/               # Frontend tests
        ├── GardenCard.test.tsx
        ├── TypeBadge.test.tsx
        ├── NotificationItem.test.tsx
        └── api.test.ts
```
