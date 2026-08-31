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
