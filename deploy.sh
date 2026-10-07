#!/usr/bin/env bash
# Fast deploy to the javi server: rsync code + .env + images, then
# docker compose up -d --build on the server.
#
#   ./deploy.sh            # deploy to the default host (javi)
#   DEPLOY_HOST=other ./deploy.sh
set -euo pipefail

HOST="${DEPLOY_HOST:-javi}"
REMOTE_DIR="~/www-sites/gardener"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Syncing code to $HOST:$REMOTE_DIR (incremental, --delete)..."
ssh "$HOST" "mkdir -p $REMOTE_DIR/images"
rsync -az --delete \
  --exclude .git \
  --exclude node_modules \
  --exclude .next \
  --exclude __pycache__ \
  --exclude '*.pyc' \
  --exclude .venv \
  --exclude .env \
  --exclude 'deploy/env.javi' \
  --exclude db.sqlite3 \
  --exclude media \
  --exclude images \
  --exclude 'diff*.txt' \
  "$ROOT/" "$HOST:$REMOTE_DIR/"

echo "==> Syncing .env (deploy/env.javi -> .env)..."
rsync -az "$ROOT/deploy/env.javi" "$HOST:$REMOTE_DIR/.env"

echo "==> Syncing local images to $REMOTE_DIR/images (additive, never deletes server uploads)..."
rsync -az "$ROOT/backend/media/" "$HOST:$REMOTE_DIR/images/"

echo "==> Building and starting containers on $HOST..."
ssh "$HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.deploy.yml up -d --build"

echo
echo "==> Status:"
ssh "$HOST" "cd $REMOTE_DIR && docker compose -f docker-compose.deploy.yml ps"

echo
echo "==> Health checks:"
ssh "$HOST" "curl -s -o /dev/null -w 'backend  :8000/api/v1/garden/ -> %{http_code}\n' http://localhost:8000/api/v1/garden/; curl -s -o /dev/null -w 'frontend :3000/                 -> %{http_code}\n' http://localhost:3000/"

echo
echo "Deploy done. Site: http://192.168.10.65:3000"
