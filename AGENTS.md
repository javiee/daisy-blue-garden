# AGENTS.md — DaisyBlue Gardener

Operational runbook for AI sessions. Architecture and API docs live in `CLAUDE.md`.

## Deployment (fast loop)

**One command from the repo root:**

```bash
./deploy.sh
```

What it does, in order:
1. `rsync -az --delete` code → `javi:~/www-sites/gardener/` (excludes `.git`, `node_modules`, `.next`, `__pycache__`, `.env`, `db.sqlite3`, `media/`, `diff*.txt`)
2. `rsync deploy/env.javi` → `javi:~/www-sites/gardener/.env`
3. `rsync backend/media/` → `javi:~/www-sites/gardener/images/` **additively** (no `--delete` — never removes photos uploaded via the server)
4. `ssh javi 'docker compose -f docker-compose.deploy.yml up -d --build'` + health checks

- **Server:** ssh host `javi` = 192.168.10.65 (user `jcaro`, key `~/.ssh/javi`)
- **Stack on server:** `backend` (gunicorn, :8000) + `qcluster` (django-q worker) + `frontend` (Next.js, :3000) — defined in `docker-compose.deploy.yml`
- **Site:** http://192.168.10.65:3000 · **API:** http://192.168.10.65:8000/api/v1
- **Timing:** first deploy ~3–5 min (image builds); subsequent deploys ~10–30s (layer caching)
- **`deploy/env.javi`** is gitignored and is the source of truth for server env (SECRET_KEY, DB URL, LLM key, Telegram, `ALLOWED_HOSTS`). When you change any of these keys locally, update `deploy/env.javi` too, or the server keeps the old values.
- **Database:** MariaDB running on javi itself (`mysql://gardener@192.168.10.65:3306/gardener`, same host as the app). Migrations run automatically at backend container start (`backend/entrypoint.sh` waits for DB, runs `makemigrations --noinput` + `migrate`, then starts gunicorn).
- **Photos** persist at `~/www-sites/gardener/images` on the host (bind-mounted to `/app/media`, Django `MEDIA_ROOT`).

## Critical invariants

- **No Celery, no Redis.** The task queue is **django-q**, stored in MySQL (`django_q_*` tables) and consumed by the `qcluster` container. `REDIS_URL` in `.env` files is a dead leftover — ignore it. If a task "doesn't run", the problem is almost always qcluster, not Redis.
- **One SECRET_KEY everywhere.** django-q signs task payloads with Django's `SECRET_KEY`. If a task is queued from one instance (e.g. local Mac) and consumed by another (javi) with a different key, qcluster logs `BadSignature: Signature ... does not match` and drops the task. The local `.env` and `deploy/env.javi` currently share the same key on purpose — keep it that way.
- **Server `ALLOWED_HOSTS` must include `192.168.10.65`** (it's in `deploy/env.javi`). Without it Django answers 400 for LAN access.
- The frontend calls the backend from the browser at `http://<site-hostname>:8000/api/v1` (see `frontend/lib/api.ts`); the backend's 8000 port must be reachable on that hostname and allowed in `ALLOWED_HOSTS`.

## Troubleshooting

Run from your machine unless noted:

```bash
# Container status (on server)
ssh javi 'cd ~/www-sites/gardener && docker compose -f docker-compose.deploy.yml ps'

# Logs
ssh javi 'docker logs --tail 50 gardener-backend-1'
ssh javi 'docker logs --tail 50 gardener-qcluster-1'
ssh javi 'docker logs --tail 50 gardener-frontend-1'

# Health
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.10.65:8000/api/v1/garden/   # want 200
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.10.65:3000/                  # want 200

# Rebuild/restart a single service (on server)
ssh javi 'cd ~/www-sites/gardener && docker compose -f docker-compose.deploy.yml up -d --build backend'
```

| Symptom | Cause / fix |
|---|---|
| qcluster not running | It only starts when `backend` is **healthy** (depends_on healthcheck). Check `docker compose ps` for backend health state and its logs. |
| `BadSignature` in qcluster logs | SECRET_KEY mismatch between the instance that queued the task and the one consuming it. Make both `.env` files share the same key (see invariants). |
| Task queued but never processed | Check qcluster is up; check `OrmQ` backlog: `ssh javi 'cd ~/www-sites/gardener && docker exec gardener-backend-1 python manage.py shell -c "from django_q.models import OrmQ; print(OrmQ.objects.count())"'` |
| LLM generation hangs on the UI (Add Plant / Regenerate Care) | Same as above — it's an async task. The UI polls and gives up after 90s. Verify qcluster consumed it (`docker logs gardener-qcluster-1 | tail`). |
| API returns 400 Bad Request | `ALLOWED_HOSTS` doesn't include the hostname used (server: add to `deploy/env.javi`, redeploy). |
| Frontend can't reach API | Browser needs `<host>:8000` open and allowed; check backend port mapping and `ALLOWED_HOSTS`. |
| Migrations missing on server | They run at backend start automatically; if the backend is stuck on "Waiting for database", check the DB credentials in the server `.env` and that MariaDB is up: `ssh javi 'docker ps --filter name=mariadb'`. |
| Photos missing after deploy | They live in `~/www-sites/gardener/images` on the host (not in git). Local → server sync is additive only via `deploy.sh`. |

## Local development

```bash
# Backend (needs deps: python3 with django, mysqlclient, django_q, etc.)
cd backend && python3 manage.py runserver
# Frontend
cd frontend && npm install && npm run dev
```

- **Local `.env` is at the repo root**, but Django reads `backend/.env` (see `environ.Env.read_env` in `backend/config/settings/base.py`) — which does not exist, so local runs fall back to the sqlite default (`DATABASE_URL` unset). To run locally against the shared MySQL, export the vars first, e.g. `set -a; source .env; set +a` in `backend/`.
- **There is no local qcluster** — locally queued tasks are consumed by **javi's** qcluster (same DB). That only works because the SECRET_KEYs match (see invariants).
- `npm test` in `frontend/` runs Vitest in **watch mode**; for one-shot runs use `npx vitest run`.
- Tests: `cd backend && python3 manage.py test` (84 tests) · `cd frontend && npx tsc --noEmit` · `cd frontend && npx vitest run`

## Housekeeping

- `diff.txt` / `diff-all.txt` in the repo root are one-off migration artifacts (already applied) — safe to delete.
- Stopped orphan container `gardener_db_1` on javi (leftover, 4 months old): `ssh javi 'docker rm gardener_db_1'` to clean up.
- The `~/repos/daisy-blue-garden` clone on javi is unused by the deploy (deploy target is `~/www-sites/gardener/`).
