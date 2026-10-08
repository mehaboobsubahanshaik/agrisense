#!/usr/bin/env bash
# Nightly backup of the database and uploaded crop photos.
# Cron:  0 2 * * *  /opt/agrisense/scripts/backup.sh
set -euo pipefail
STAMP=$(date +%Y%m%d-%H%M%S)
DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$DIR"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-agri}" "${POSTGRES_DB:-agrisense}" \
  | gzip > "$DIR/db-$STAMP.sql.gz"

docker run --rm -v agrisense-ai_uploads:/data -v "$(pwd)/$DIR":/backup alpine \
  tar czf "/backup/uploads-$STAMP.tar.gz" -C /data .

find "$DIR" -name '*.gz' -mtime +14 -delete
echo "Backup written to $DIR (db-$STAMP.sql.gz, uploads-$STAMP.tar.gz)"
