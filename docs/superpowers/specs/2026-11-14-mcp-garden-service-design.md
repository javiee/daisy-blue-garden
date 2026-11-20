# MCP Garden Service — Design

Date: 2026-11-14 · Size: small change

## Intent

Let an external AI client (Claude Desktop, OpenCode, any MCP client on the LAN) talk to
the garden app in plain language: "what's in my garden?", "what care is due this week?",
"add a pruning event for the fig tree". The MCP server is a thin tool layer over the
existing Django data — it exposes what exists, it does not recompute or reclassify.

## Goals

- MCP server speaking **streamable HTTP** on the same host as the backend, reachable at
  `http://192.168.10.65:8001/mcp` (LAN).
- Tools (Approach A — raw data, client model does the grouping):
  - `list_garden_items(type?, search?)` — name, type, description, cares text, photo URL,
    event count.
  - `get_garden_item(item_id)` — full details including all calendar events.
  - `list_care_events(item_id?, event_type?, from_date?, to_date?)` — care calendar
    (defaults to upcoming 6 months).
  - `add_care_event(item_id, title, date, event_type, recurrence?, description?)` —
    create a calendar event on a plant.
- Deploys with the existing `./deploy.sh`; no new Docker image, no new infra beyond one
  service in `docker-compose.deploy.yml`.
- Plain-function tool logic, covered by backend tests (Django `TestCase`).

## Non-goals

- No structured soil/fertilizer/light fields (Approach B — separate future project;
  grouping by those attributes is done by the client model reading the `cares` text).
- No authentication (consistent with the rest of the app: open on the LAN).
- No mutation of `GardenItem` itself (no plant create/update/delete, no photo upload,
  no LLM care regeneration via MCP) — care events only.
- No pagination in tool responses: lists are capped (e.g. 50 items) with a count.

## Anti-goals

- Must not change or break the existing REST API or its consumers.
- Must not add LLM calls inside MCP tools (no per-query classification).

## Constraints

- The backend runs **gunicorn (WSGI)**; MCP streamable HTTP is ASGI-only. The MCP server
  therefore runs as its **own service** using the existing backend image with a different
  command, on port **8001**.
- The MCP server uses the **Django ORM directly** (initializes the same settings module,
  same DB) rather than calling the REST API — fewer moving parts, same transactional
  semantics as the rest of the app.

## Approaches (decided in conversation)

1. **A. Expose raw data, client model groups from text** — chosen. Cheap, works with
   today's data (name/type/cares text/events), grouping is model-side.
2. **B. Add structured fields first** (soil, water, light, fertilizer via LLM extraction)
   — rejected for now; precise grouping but new fields + LLM extraction + backfill.
   Revisit as a follow-up if grouping proves too fuzzy.
3. Hosting inside Django (same gunicorn process) — not viable: WSGI process cannot host
   the ASGI streamable-HTTP transport cleanly. Separate service in the same image is the
   clean option.

## How (builder decisions left to the implementer)

- New package `backend/mcp/` with `server.py` (FastMCP instance, tool definitions) and a
  thin entrypoint (e.g. `backend/mcp_server.py`) that configures Django and runs uvicorn
  on `0.0.0.0:8001`, stateless streamable HTTP.
- Tool logic lives in plain functions in `backend/mcp/tools.py` so tests can exercise the
  ORM queries without the MCP protocol layer.
- `requirements.txt`: add `mcp` and `uvicorn`.
- `docker-compose.deploy.yml`: new `mcp` service — same `build: ./backend`,
  `entrypoint: []`, `command: python mcp_server.py`, port `8001:8001`,
  `depends_on: backend: service_healthy`, `restart: unless-stopped`.
- Docs: add MCP section to `CLAUDE.md` (endpoint, tools, env), note the new service and
  port in `AGENTS.md` (troubleshooting + invariants).
- Left to the implementer: exact tool argument schemas, tool description text (these are
  what the client model reads — write them for an LLM audience), error wording, list caps.
