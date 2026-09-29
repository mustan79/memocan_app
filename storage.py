from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from config import config_dir
from datetime import datetime

class StatsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or config_dir() / "stats.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS daily (day TEXT PRIMARY KEY, active_seconds INTEGER DEFAULT 0, water_count INTEGER DEFAULT 0, away_seconds INTEGER DEFAULT 0)")
            columns = {row[1] for row in db.execute("PRAGMA table_info(daily)")}
            if "pc_seconds" not in columns:
                db.execute("ALTER TABLE daily ADD COLUMN pc_seconds INTEGER DEFAULT 0")
            db.execute("CREATE TABLE IF NOT EXISTS conversation (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL)")
    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_usage(self, rows: dict):
        """Persist sampled active/idle/awake seconds, already split at midnight."""
        with self._connect() as db:
            for day, values in rows.items():
                active, away, pc = values
                db.execute("""INSERT INTO daily(day,active_seconds,away_seconds,pc_seconds)
                    VALUES(?,?,?,?) ON CONFLICT(day) DO UPDATE SET
                    active_seconds=active_seconds+excluded.active_seconds,
                    away_seconds=away_seconds+excluded.away_seconds,
                    pc_seconds=pc_seconds+excluded.pc_seconds""",
                    (day, active, away, pc))

    def daily_metrics(self, day: date) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT active_seconds,away_seconds,water_count,pc_seconds FROM daily WHERE day=?",
                             (day.isoformat(),)).fetchone() or (0, 0, 0, 0)
        return dict(zip(("active_seconds", "away_seconds", "water_count", "pc_seconds"), row))

    def week_metrics(self, day: date) -> tuple[dict, list]:
        monday = day - timedelta(days=day.weekday())
        days = [(monday + timedelta(days=i)) for i in range(7)]
        with self._connect() as db:
            rows = db.execute("SELECT day,active_seconds,away_seconds,water_count,pc_seconds FROM daily WHERE day BETWEEN ? AND ?",
                              (days[0].isoformat(), days[-1].isoformat())).fetchall()
        names = ("active_seconds", "away_seconds", "water_count", "pc_seconds")
        indexed = {row[0]: dict(zip(names, row[1:])) for row in rows}
        detail = [(d, indexed.get(d.isoformat(), dict.fromkeys(names, 0))) for d in days]
        return {key: sum(values[key] for _, values in detail) for key in names}, detail

    def available_weeks(self, today: date | None = None) -> list[date]:
        today = today or date.today()
        current = today - timedelta(days=today.weekday())
        with self._connect() as db:
            earliest = db.execute("SELECT MIN(day) FROM daily").fetchone()[0]
        first = date.fromisoformat(earliest) if earliest else today
        first -= timedelta(days=first.weekday())
        return [current - timedelta(weeks=i) for i in range(max(0, (current-first).days//7)+1)]
    def add_active(self, seconds: int, away_seconds: int = 0):
        if seconds <= 0 and away_seconds <= 0: return
        with self._connect() as db:
            db.execute("INSERT INTO daily(day,active_seconds,away_seconds) VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET active_seconds=active_seconds+excluded.active_seconds, away_seconds=away_seconds+excluded.away_seconds", (date.today().isoformat(), max(0, seconds), max(0, away_seconds)))
    def add_water(self, count: int = 1) -> int:
        count = max(1, min(20, int(count)))
        with self._connect() as db:
            db.execute("INSERT INTO daily(day,water_count) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET water_count=water_count+excluded.water_count", (date.today().isoformat(), count))
            return db.execute("SELECT water_count FROM daily WHERE day=?", (date.today().isoformat(),)).fetchone()[0]
    def today_water(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT water_count FROM daily WHERE day=?", (date.today().isoformat(),)).fetchone()
        return row[0] if row else 0
    def add_conversation(self, role: str, content: str):
        timestamp = datetime.now().isoformat(timespec="seconds")
        with self._connect() as db:
            db.execute("INSERT INTO conversation(created_at,role,content) VALUES(?,?,?)", (timestamp, role, content))
        path = config_dir() / "conversations.md"
        if path.exists() and path.stat().st_size > 200_000:
            archive = config_dir() / f"conversations-{datetime.now():%Y%m%d-%H%M%S}.md"
            path.replace(archive)
        label = "Kullanıcı" if role == "user" else "Memocan"
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"\n### {timestamp} — {label}\n\n{content.strip()}\n")
    def recent_conversation(self, limit: int = 12) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT role,content FROM conversation ORDER BY id DESC LIMIT ?", (max(1, limit),)).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]
    def weekly(self) -> dict:
        since = (date.today() - timedelta(days=6)).isoformat()
        with self._connect() as db:
            row = db.execute("SELECT COALESCE(SUM(active_seconds),0),COALESCE(SUM(away_seconds),0),COALESCE(SUM(water_count),0) FROM daily WHERE day>=?", (since,)).fetchone()
        return {"active_seconds": row[0], "away_seconds": row[1], "water_count": row[2]}
