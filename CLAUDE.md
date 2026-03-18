# DaisyBlue Gardener — Technical Documentation

## Project Overview

DaisyBlue Gardener is an AI-powered garden administration application that helps users manage their plants and trees. When a new plant is added, an LLM automatically generates a description and care guide. Based on this, the application creates a calendar of actionable care events and sends reminders via Telegram.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 15)                │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Garden  │  │ Calendar │  │Notif. Page │  │  Add     │ │
│  │   List   │  │Week/Month│  │ + Settings │  │  Plant   │ │
│  └──────────┘  └──────────┘  └────────────┘  └──────────┘ │
│          React Query + Tailwind CSS + TypeScript            │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST API
                      │ http://localhost:8000/api/v1
┌─────────────────────▼───────────────────────────────────────┐
│                    Backend (Django 5 + DRF)                 │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐ │
│  │  garden  │  │  events  │  │    llm     │  │ notifs   │ │
│  │   app    │  │   app    │  │    app     │  │   app    │ │
│  └──────────┘  └──────────┘  └────────────┘  └──────────┘ │
│                   Celery + Redis (async tasks)              │
└──────┬──────────────────────────┬───────────────────────────┘
       │                          │
┌──────▼──────┐          ┌────────▼────────┐
│    MySQL    │          │  LLM Provider   │
│  Database   │          │ OpenAI/Anthropic│
└─────────────┘          │    /Ollama      │
                         └────────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Telegram Bot   │
                         └─────────────────┘
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | Django | ≥5.1 |
| REST API | Django REST Framework | ≥3.15 |
| Database | MySQL | 8.0 |
| Async tasks | Celery + Redis | ≥5.4 |
| LLM integration | OpenAI / Anthropic / Ollama | Latest |
| Notifications | python-telegram-bot | ≥21.9 |
| Frontend framework | Next.js | ≥15.1 |
| UI | Tailwind CSS | v4 |
| Data fetching | TanStack React Query | v5 |
| Forms | React Hook Form + Zod | Latest |
| Testing (backend) | Django TestCase | Built-in |
| Testing (frontend) | Vitest + React Testing Library | Latest |
| Containerization | Docker + docker-compose | Latest |
| CI/CD | GitHub Actions | Latest |

---

## Design Decisions

### LLM Provider Abstraction
The LLM integration uses a provider pattern (`BaseLLMProvider`) that supports OpenAI, Anthropic, and Ollama (local). Switching providers requires only changing the `LLM_PROVIDER` env var — no code changes needed. This makes the app deployable in air-gapped environments using Ollama.

### Async LLM Generation
LLM calls can take 5-30 seconds. To avoid blocking the API response, generation is offloaded to a Celery task triggered via a Django signal on `GardenItem` creation. The frontend polls for updates.

### Notification System
Celery Beat runs the `check_and_send_notifications` task on a configurable schedule. The `NotificationConfig` model stores the schedule and Telegram chat ID. Acknowledged notifications are suppressed until the next calculated occurrence date based on event recurrence.

### Calendar Events
Events have four recurrence types: once, weekly, monthly, yearly. The LLM generates a structured JSON schedule, which is parsed and stored as individual `CalendarEvent` records. The scheduler can also expand recurring events up to 6 months ahead.

---

## Database Schema

### GardenItem
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| name | CharField(200) | Plant/tree name |
| type | CharField(20) | plant / tree / shrub / other |
| description | TextField | AI-generated description |
| cares | TextField | AI-generated care guide |
| photo | ImageField | Optional photo |
| created_at | DateTimeField | Auto |
| updated_at | DateTimeField | Auto |

### CalendarEvent
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| item | FK(GardenItem) | Related plant |
| title | CharField(200) | Event title |
| description | TextField | Instructions |
| date | DateField | When to perform |
| recurrence | CharField(20) | once/weekly/monthly/yearly |
| event_type | CharField(20) | watering/fertilizing/pruning/other |
| created_at | DateTimeField | Auto |

### NotificationConfig
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| telegram_chat_id | CharField(100) | Target Telegram chat |
| frequency | CharField(20) | daily/weekly/monthly |
| days_before | IntegerField | Alert N days before event |
| is_active | BooleanField | Enable/disable |

### Notification
| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| event | FK(CalendarEvent) | Related event |
| config | FK(NotificationConfig) | Which config sent it |
| telegram_message_id | CharField | Telegram message ID |
| status | CharField | pending/sent/failed |
| sent_at | DateTimeField | When sent |
| acknowledged | BooleanField | User acknowledged |
| acknowledged_at | DateTimeField | When acknowledged |
| next_occurrence_date | DateField | When to notify again |

---

## API Documentation

### Garden Items

```
GET  /api/v1/garden/              List all garden items (paginated)
  Query params: ?type=plant&search=rose&ordering=-created_at

POST /api/v1/garden/              Create a new garden item
  Body: multipart/form-data { name, type, photo? }
  → Triggers LLM care generation asynchronously

GET  /api/v1/garden/{id}/        Get a single item
PUT  /api/v1/garden/{id}/        Update an item
DELETE /api/v1/garden/{id}/      Delete an item
```

### Calendar Events

```
GET  /api/v1/events/             List events
  Query params: ?week=2024-W01 | ?month=2024-01 | ?item=1 | ?event_type=watering

POST /api/v1/events/             Create event
GET  /api/v1/events/{id}/       Get event
PUT  /api/v1/events/{id}/       Update event
DELETE /api/v1/events/{id}/     Delete event

GET  /api/v1/events/by-item/{item_id}/   Events for a specific plant
```

### LLM

```
POST /api/v1/llm/generate-care/{item_id}/   Trigger care generation
  → Returns { task_id, status: "queued" }

GET  /api/v1/llm/providers/                 List available LLM providers
```

### Notifications

```
GET  /api/v1/notifications/                List all notifications
GET  /api/v1/notifications/pending/        List unacknowledged notifications
POST /api/v1/notifications/{id}/acknowledge/   Acknowledge a notification

GET  /api/v1/notifications/config/         Get notification configs
POST /api/v1/notifications/config/         Create notification config
```

---

## Environment Variables

```bash
# Django
SECRET_KEY=                     # Django secret key (required in production)
DEBUG=True                      # Set False in production
ALLOWED_HOSTS=localhost          # Comma-separated list
DATABASE_URL=mysql://user:pass@host:3306/dbname

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
LLM_PROVIDER=openai             # openai | anthropic | ollama
LLM_API_KEY=sk-...              # API key for OpenAI or Anthropic
LLM_MODEL=gpt-4o                # Model to use
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama

# Telegram
TELEGRAM_BOT_TOKEN=             # From @BotFather
TELEGRAM_CHAT_ID=               # Your Telegram chat ID

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- MySQL 8.0 (or use Docker)
- Redis (or use Docker)

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp ../.env.example .env
# Edit .env with your settings

# 4. Run database migrations
python manage.py migrate

# 5. Create admin user
python manage.py createsuperuser

# 6. Start dev server
python manage.py runserver

# 7. Start Celery worker (separate terminal)
celery -A celery worker -l info

# 8. Start Celery Beat scheduler (separate terminal)
celery -A celery beat -l info
```

### Frontend Setup

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend available at http://localhost:3000

### Running Tests

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

---

## Docker Deployment

### Quick Start

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user
docker-compose exec backend python manage.py createsuperuser
```

### Services
| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | Django API |
| frontend | 3000 | Next.js UI |
| db | 3306 | MySQL 8.0 |
| redis | 6379 | Celery broker |
| celery | - | Async task worker |
| celery-beat | - | Task scheduler |

---

## LLM Provider Setup

### OpenAI
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-api-key
LLM_MODEL=gpt-4o        # or gpt-4o-mini for cost savings
```

### Anthropic
```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-your-api-key
LLM_MODEL=claude-sonnet-4-6
```

### Ollama (Local, Free)
```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.2

LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Telegram Bot Setup

1. Message `@BotFather` on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token to `TELEGRAM_BOT_TOKEN`
4. Start a chat with your bot or add it to a group
5. Get your chat ID: message `@userinfobot`
6. Set `TELEGRAM_CHAT_ID` to your chat ID
7. Configure `NotificationConfig` via the app's Notifications page

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. **test-backend** — Runs Django tests against a MySQL test database
2. **test-frontend** — Runs Vitest tests
3. **build-and-push** (main branch only) — Builds and pushes Docker images to GitHub Container Registry

Images tagged with:
- `latest` — always points to the most recent main build
- `sha-{commit}` — immutable tag for specific builds

---

## Feature Roadmap

- [ ] Plant photo gallery with multiple images
- [ ] Weather API integration for smart watering reminders
- [ ] Plant disease detection via image recognition
- [ ] Export garden journal to PDF
- [ ] Multi-user support with shared gardens
- [ ] Plant marketplace/trading between users
- [ ] Push notifications (Web Push) in addition to Telegram
