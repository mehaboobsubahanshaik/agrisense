#!/usr/bin/env bash
# One-command startup with a readiness wait, so the demo never opens on a blank page.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] || { cp .env.example .env; echo "Created .env from the example."; }

docker compose up --build -d
PORT="${HTTP_PORT:-8080}"

printf 'Waiting for the stack'
for _ in $(seq 1 90); do
  if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; then
    echo; echo "AgriSense AI is up:"
    echo "  App        http://localhost:${PORT}"
    echo "  API docs   http://localhost:${PORT}/docs"
    echo "  Grafana    http://localhost:3001  (admin / ${GRAFANA_PASSWORD:-admin})"
    echo
    echo "Sign in with any 10-digit number. In DEV_MODE the code is shown on screen"
    echo "and printed by:  docker compose logs -f backend"
    exit 0
  fi
  printf '.'; sleep 2
done
echo; echo "Timed out. Check: docker compose logs --tail=80"; exit 1
