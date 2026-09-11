"""Merge estate records from the verified 2026-08-28 database snapshot."""
from datetime import datetime
from pathlib import Path
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "aegis.db"
SOURCE = ROOT / "backups" / "aegis_20260828_131825.db"
BACKUP = ROOT / "backups" / f"aegis_before_restore_{datetime.now():%Y%m%d_%H%M%S}.db"

if not TARGET.exists():
    raise SystemExit(f"Missing target database: {TARGET}")
if not SOURCE.exists():
    raise SystemExit(f"Missing source database: {SOURCE}")

shutil.copy2(TARGET, BACKUP)
with sqlite3.connect(TARGET) as db:
    db.execute("ATTACH DATABASE ? AS source_db", (str(SOURCE),))
    for table in ("zones", "sensors", "sensor_data"):
        db.execute(f"INSERT OR IGNORE INTO {table} SELECT * FROM source_db.{table}")
    db.commit()
    print(f"Backup created: {BACKUP.name}")
    for table in ("zones", "sensors", "sensor_data"):
        print(f"{table}: {db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]}")
