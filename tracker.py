import ctypes
import time
from datetime import datetime, timedelta


def awake_clock() -> float:
    """Windows working-state time excludes sleep/hibernation."""
    if hasattr(ctypes, "windll"):
        ticks = ctypes.c_ulonglong()
        if ctypes.windll.kernel32.QueryUnbiasedInterruptTime(ctypes.byref(ticks)):
            return ticks.value / 10_000_000
    return time.monotonic()


class UsageTracker:
    def __init__(self, store, clock=awake_clock, now=datetime.now):
        self.store, self.clock, self.now = store, clock, now
        self.last_clock = clock()
        self.pending = {}
        self.since_flush = 0

    def sample(self, active: bool):
        current = self.clock()
        seconds = max(0, int(current - self.last_clock))
        if seconds == 0:
            return 0
        self.last_clock += seconds
        # A stopped UI must not infer hours of user activity from one input sample.
        seconds = min(seconds, 5)
        end = self.now()
        start = end - timedelta(seconds=seconds)
        while start < end:
            boundary = min(end, datetime.combine(start.date()+timedelta(days=1), datetime.min.time()))
            duration = (boundary-start).total_seconds()
            row = self.pending.setdefault(start.date().isoformat(), [0, 0, 0])
            row[0 if active else 1] += duration
            row[2] += duration
            start = boundary
        self.since_flush += seconds
        if self.since_flush >= 15:
            self.flush()
        return seconds

    def flush(self):
        if self.pending:
            self.store.add_usage(self.pending)
            self.pending = {}
        self.since_flush = 0


class WorkTimer:
    def __init__(self, minutes: int, elapsed: int = 0):
        self.threshold = max(1, minutes * 60)
        self.elapsed = max(0, elapsed)

    def set_minutes(self, minutes: int):
        self.threshold = max(1, minutes * 60)

    def advance(self, active: bool, seconds: int = 1) -> bool:
        if not active: return False
        self.elapsed += max(0, seconds)
        if self.elapsed >= self.threshold:
            self.elapsed %= self.threshold
            return True
        return False
