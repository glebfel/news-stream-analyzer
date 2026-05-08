#!/usr/bin/env bash
# Manual deploy helper. Run from a developer machine that has SSH access to the server.
#
# Usage:
#   DEPLOY_HOST=user@1.2.3.4 ./scripts/deploy.sh
#
# Assumes the repo is already cloned on the server at /opt/news-stream-analyzer
# and the production .env is in place. See docs/deployment.md for first-time setup.

set -euo pipefail

: "${DEPLOY_HOST:?DEPLOY_HOST not set, e.g. user@1.2.3.4}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/news-stream-analyzer}"
COMPOSE_ARGS="-f docker-compose.yml -f docker-compose.prod.yml"

echo "==> Deploying to ${DEPLOY_HOST}:${DEPLOY_PATH}"

ssh "$DEPLOY_HOST" bash <<EOF
set -euo pipefail
cd "$DEPLOY_PATH"

echo "==> git pull"
git pull --ff-only origin master

echo "==> docker compose build"
docker compose $COMPOSE_ARGS build

echo "==> docker compose up -d"
docker compose $COMPOSE_ARGS up -d --remove-orphans

echo "==> waiting 15s for OpenSearch and Neo4j to become healthy"
sleep 15

echo "==> applying migrations"
docker compose $COMPOSE_ARGS exec -T api-gateway python /app/scripts/migrate.py || \
  echo "WARN: migrate.py not run inside container — run from the project root on host instead"

echo "==> service status"
docker compose $COMPOSE_ARGS ps
EOF

echo "==> Done."
