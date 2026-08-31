from __future__ import annotations
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from config import config_dir

class StatsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or config_dir() / "stats.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, active_seconds INTEGER DEFAULT 0, water_count INTEGER DEFAULT 0, away_seconds INTEGER DEFAULT 0)")
    def _connect(self): return sqlite3.connect(self.path)
    def add_active(self, seconds: int, away_seconds: int = 0):
        if seconds <= 0 and away_seconds <= 0: return
        with self._connect() as db:
            db.execute("INSERT INTO daily(day,active_seconds,away_seconds) VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET active_seconds=active_seconds+excluded.active_seconds, away_seconds=away_seconds+excluded.away_seconds", (date.today().isoformat(), max(0, seconds), max(0, away_seconds)))
    def add_water(self) -> int:
        with self._connect() as db:
            db.execute("INSERT INTO daily(day,water_count) VALUES(?,1) ON CONFLICT(day) DO UPDATE SET water_count=water_count+1", (date.today().isoformat(),))
            return db.execute("SELECT water_count FROM daily WHERE day=?", (date.today().isoformat(),)).fetchone()[0]
    def weekly(self) -> dict:
        since = (date.today() - timedelta(days=6)).isoformat()
        with self._connect() as db:
            row = db.execute("SELECT COALESCE(SUM(active_seconds),0),COALESCE(SUM(away_seconds),0),COALESCE(SUM(water_count),0) FROM daily WHERE day>=?", (since,)).fetchone()
        return {"active_seconds": row[0], "away_seconds": row[1], "water_count": row[2]}
