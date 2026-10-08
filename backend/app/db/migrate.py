"""Tiny forward-only migrations.

Base.metadata.create_all creates missing tables but never alters existing ones,
so anyone who already ran the stack would keep an old chat_history table and hit
a column error the moment they attached a photo. These statements are all
IF NOT EXISTS, so they are safe on every boot and on a fresh database alike.

Once the schema settles, move this to Alembic (alembic.ini is already scaffolded).
"""
import logging

from sqlalchemy import text

from app.db.session import engine

log = logging.getLogger(__name__)

STATEMENTS = [
    "ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS attachment JSON",
    "ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS engine VARCHAR(48)",
    "ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS last_verified TIMESTAMPTZ",
    "ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS link_status VARCHAR(24)",
    "ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS source_note VARCHAR(255)",
    "ALTER TABLE government_schemes ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
]


async def run() -> None:
    async with engine.begin() as conn:
        for sql in STATEMENTS:
            try:
                await conn.execute(text(sql))
            except Exception as exc:      # never block startup on a migration
                log.warning("migration skipped (%s): %s", sql, exc)
