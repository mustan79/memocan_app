import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from storage import StatsStore
from tracker import UsageTracker


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'stats.sqlite3'

    def tearDown(self):
        self.tmp.cleanup()

    def test_upgrade_preserves_existing_water_and_active(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE daily(day TEXT PRIMARY KEY, active_seconds INTEGER, water_count INTEGER, away_seconds INTEGER)')
            db.execute('INSERT INTO daily VALUES (?,?,?,?)', ('2026-09-28', 3600, 4, 30))
        db.close()
        store = StatsStore(self.path)
        self.assertEqual(store.daily_metrics(date(2026, 9, 28)),
                         dict(active_seconds=3600, away_seconds=30, water_count=4, pc_seconds=0))

    def test_calendar_week_not_rolling_seven_days_and_water_one_click(self):
        store = StatsStore(self.path)
        store.add_usage({'2026-09-27': [100, 0, 100], '2026-09-28': [60, 30, 90]})
        total, days = store.week_metrics(date(2026, 9, 29))
        self.assertEqual(total['pc_seconds'], 90)
        self.assertEqual(days[0][0], date(2026, 9, 28))
        self.assertEqual(days[-1][0], date(2026, 10, 4))
        self.assertEqual(len(days), 7)
        self.assertEqual(store.available_weeks(date(2026, 9, 29)), [date(2026, 9, 28), date(2026, 9, 21)])
        self.assertEqual(store.add_water(), 1)
        self.assertEqual(store.add_water(), 2)

    def test_sample_splits_midnight_and_flush_does_not_double_count(self):
        store = StatsStore(self.path)
        clock = [0]
        tracker = UsageTracker(store, clock=lambda: clock[0], now=lambda: datetime(2026, 9, 29, 0, 0, 1))
        clock[0] = 2
        tracker.sample(True)
        tracker.flush(); tracker.flush()
        self.assertEqual(store.daily_metrics(date(2026, 9, 28))['active_seconds'], 1)
        self.assertEqual(store.daily_metrics(date(2026, 9, 29))['pc_seconds'], 1)

    def test_sleep_not_added_to_awake_time_and_idle_samples_accumulate(self):
        store = StatsStore(self.path)
        clock, wall = [0], [datetime(2026, 9, 29, 10)]
        tracker = UsageTracker(store, clock=lambda: clock[0], now=lambda: wall[0])
        for _ in range(20):
            clock[0] += 1; wall[0] += timedelta(seconds=1)
            tracker.sample(False)
        wall[0] += timedelta(hours=8)
        tracker.sample(False)
        tracker.flush()
        self.assertEqual(store.daily_metrics(wall[0].date())['pc_seconds'], 20)
        self.assertEqual(store.daily_metrics(wall[0].date())['away_seconds'], 20)
        self.assertEqual(store.daily_metrics(wall[0].date())['active_seconds'], 0)


if __name__ == '__main__': unittest.main()
