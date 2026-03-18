# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **Inline plant page editing** — The plant detail page is now fully editable without leaving the page:
  - **Description** — hover over the About section to reveal a pencil icon; click to enter edit mode (textarea + Save / Cancel).
  - **Care Guide** — same inline edit pattern; a trash icon in the section header clears the care guide entirely.
  - **Photo upload / replace** — hover over the photo (or the placeholder) to reveal a camera overlay; clicking opens a native file picker. Works for both first upload and replacing an existing photo.
- `api.garden.patch` — new PATCH (partial update) helper for JSON fields.
- `api.garden.patchPhoto` — new PATCH helper that sends a `multipart/form-data` body for photo upload.
- `usePatchGardenItem` and `usePatchGardenItemPhoto` React Query mutation hooks.
- `InlineTextEdit` component (co-located in the plant detail page) providing a reusable hover-to-edit pattern.

### Added — Delete care events from plant page

- **Delete button on event cards** — A trash icon appears on hover for each care event in the plant detail page. Clicking it shows an inline confirm (✓ / ✗) to prevent accidental deletions.
- `useDeleteEvent(itemId)` React Query mutation hook — calls `DELETE /api/v1/events/{id}/` and invalidates the item's event list on success.
- `EventCard` now accepts an optional `onDelete` prop; when omitted (e.g. calendar page) the delete control is not rendered.

### Added — Manual care event creation — Users can now add care events directly from the plant detail page via an "Add Event" button in the Care Schedule section. A modal form accepts title, description, date, event type (watering / fertilizing / pruning / other), and recurrence (once / weekly / monthly / yearly).
- **Manual event protection** — Events added manually are flagged with `is_manual = true` and are never deleted when the "Regenerate Care" button is clicked. Only AI-generated events (`is_manual = false`) are replaced on regeneration.
- **"Manual" badge on event cards** — Manually created events display an amber "Manual" badge in the care schedule list so users can distinguish them from AI-generated events.

### Changed

- `CalendarEvent` model: added `is_manual` boolean field (default `false`).
- `generate_item_care_async` Celery task: scoped the pre-regeneration delete to `is_manual=False` events only.

### Migration

- `backend/apps/events/migrations/0002_calendarevent_is_manual.py` — adds the `is_manual` column to the `events_calendarevent` table.

---

## [0.1.0] — 2026-03-18

### Added

- **Garden management** — Create, list, and view plants/trees/shrubs with optional photo upload.
- **AI care generation** — On item creation a Celery task calls the configured LLM provider (OpenAI, Anthropic, or Ollama) to generate a description, care guide, and structured care schedule automatically.
- **LLM provider abstraction** — Switch between OpenAI, Anthropic, and Ollama by changing a single env var (`LLM_PROVIDER`). No code changes required.
- **Calendar events** — Care schedules are stored as `CalendarEvent` records with four recurrence types (once, weekly, monthly, yearly) and four event types (watering, fertilizing, pruning, other).
- **Week/month calendar view** — Frontend calendar page with week and month navigation filtering events by date range.
- **Telegram notifications** — Celery Beat periodically checks upcoming events and sends reminders via a Telegram bot. Users can acknowledge notifications and configure frequency and lead time.
- **Regenerate Care button** — Trigger a fresh LLM-generated care schedule for any plant from its detail page.
- **Docker Compose deployment** — Full stack (Django, Celery worker, Celery Beat, MySQL, Redis, Next.js) orchestrated with `docker-compose up`.
- **GitHub Actions CI/CD** — Automated pipeline: Django test suite (with MySQL service), Vitest frontend tests, Docker image build and push to GitHub Container Registry on `main`.
- **Defensive LLM JSON parsing** — Handles markdown-fenced responses (` ```json ``` `), empty responses, and invalid JSON with detailed logging.
