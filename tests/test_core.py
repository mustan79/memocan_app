import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import MemocanApp
from llm import clean_for_speech
from storage import StatsStore
from tracker import WorkTimer

class FakeLLM:
    def __init__(self): self.history = None
    def chat(self, message, history=None): self.history = history; return "Temiz cevap."

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp.name)
        self.config_patch = patch("storage.config_dir", return_value=self.root)
        self.config_patch.start()

    def tearDown(self):
        self.config_patch.stop(); self.temp.cleanup()

    def test_work_timer_accumulates_across_idle_and_repeats(self):
        timer = WorkTimer(1)
        for _ in range(30): self.assertFalse(timer.advance(True))
        for _ in range(20): self.assertFalse(timer.advance(False))
        for _ in range(29): self.assertFalse(timer.advance(True))
        self.assertTrue(timer.advance(True))
        for _ in range(59): self.assertFalse(timer.advance(True))
        self.assertTrue(timer.advance(True))

    def test_water_count_and_query(self):
        app = MemocanApp.__new__(MemocanApp)
        app.settings = SimpleNamespace(language="tr")
        app.stats = StatsStore(self.root / "stats.sqlite3")
        app.llm = FakeLLM()
        self.assertIn("2 bardak", app._answer("2 bardak su içtim"))
        self.assertIn("2 bardak", app._answer("Bugün kaç bardak su içtim"))
        self.assertEqual(app.stats.today_water(), 2)

    def test_recent_history_is_passed_to_llm_and_markdown_is_logged(self):
        app = MemocanApp.__new__(MemocanApp)
        app.settings = SimpleNamespace(language="tr")
        app.stats = StatsStore(self.root / "stats.sqlite3")
        app.llm = FakeLLM()
        app._answer("İlk mesaj")
        app._answer("İkinci mesaj")
        self.assertEqual(len(app.llm.history), 2)
        self.assertTrue((self.root / "conversations.md").exists())

    def test_speech_cleanup(self):
        raw = "## Başlık\n- **Merhaba** [site](https://example.com) `kod`\n```python\nprint(1)\n```"
        cleaned = clean_for_speech(raw)
        for token in ("#", "*", "[", "]", "```", "https://"):
            self.assertNotIn(token, cleaned)
        self.assertIn("Merhaba", cleaned)

if __name__ == "__main__": unittest.main()
