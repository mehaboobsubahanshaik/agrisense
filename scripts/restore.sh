#!/usr/bin/env bash
# Usage: ./scripts/restore.sh backups/db-20260101-020000.sql.gz
set -euo pipefail
[ $# -eq 1 ] || { echo "Usage: $0 <db-dump.sql.gz>"; exit 1; }
gunzip -c "$1" | docker compose exec -T postgres psql -U "${POSTGRES_USER:-agri}" -d "${POSTGRES_DB:-agrisense}"
echo "Restored $1"
