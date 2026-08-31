from __future__ import annotations
import ctypes
import logging
import threading
import time
import tkinter as tk
from tkinter import ttk
from config import load_settings, save_settings
from autostart import set_startup
from hotkeys import HotkeyManager
from i18n import tr
from llm import LLMClient
from storage import StatsStore
from voice import Voice

log = logging.getLogger("memocan.app")

AVATARS = {"robot": ("🤖", "#4f8cff"), "cat": ("🐱", "#f0a05a"), "owl": ("🦉", "#9b7bd6"), "duck": ("🦆", "#f2cf4a")}

def idle_seconds() -> int:
    if not hasattr(ctypes, "windll"): return 0
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return max(0, (ctypes.windll.kernel32.GetTickCount() - info.dwTime) // 1000)
    return 0

class MemocanApp:
    def __init__(self):
        self.settings, self.stats = load_settings(), StatsStore()
        self.llm = LLMClient(self.settings)
        self.voice = Voice(self.settings.voice_enabled, self.settings.language, self.settings.microphone_index)
        self.listening, self.closing = False, False
        self.manual_voice = threading.Event()
        self.root = tk.Tk(); self.root.title("Memocan")
        self.root.overrideredirect(True); self.root.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.root, width=110, height=110, bg="#010101", highlightthickness=0, takefocus=True)
        self.canvas.pack(); self._draw_avatar()
        self.canvas.bind("<Button-1>", lambda _: self._accessible_menu())
        self.canvas.bind("<Button-3>", lambda _: self._settings_window())
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<Return>", lambda _: self._accessible_menu())
        self.last_tick, self.active_session, self.reminded = time.monotonic(), 0, False
        self.root.after(1000, self._tick)
        self.hotkeys = HotkeyManager({
            "menu": lambda: self.root.after(0, self._accessible_menu),
            "voice": lambda: self.root.after(0, self._voice_hotkey),
        })
        errors = self.hotkeys.start()
        if "menu" in errors:
            self.root.after(300, lambda: self.voice.alert(tr(self.settings.language, "hotkey_error")))
        threading.Thread(target=self._voice_loop, daemon=True, name="memocan-listener").start()

    def _draw_avatar(self):
        emoji, color = AVATARS.get(self.settings.avatar, AVATARS["robot"])
        self.canvas.create_oval(8, 8, 102, 102, fill=color, outline="white", width=2)
        self.canvas.create_text(55, 55, text=emoji, font=("Segoe UI Emoji", 42))

    def _drag(self, event):
        self.root.geometry(f"+{self.root.winfo_x()+event.x-55}+{self.root.winfo_y()+event.y-55}")

    def _voice_hotkey(self):
        log.info("Voice hotkey activated; listening=%s enabled=%s", self.listening, self.voice.enabled)
        if self.listening:
            self.voice.enabled = False
            self.settings.voice_enabled = False
            save_settings(self.settings)
            self.manual_voice.clear()
            self.voice.speak(tr(self.settings.language, "voice_off"), force=True, wait=False)
            return
        if not self.voice.enabled:
            self.voice.enabled = True
            self.settings.voice_enabled = True
            save_settings(self.settings)
        self.manual_voice.set()
        self.voice.beep()

    def _start_conversation(self):
        if not self.closing: self.manual_voice.set()

    def _conversation_worker(self):
        log.info("Conversation listening started")
        self.voice.speak(tr(self.settings.language, "listening"), force=True)
        heard, error = self.voice.listen_once()
        if heard:
            if not self.voice.enabled:
                self.listening = False; return
            answer = self._answer(heard)
            if self.voice.enabled: self.voice.speak(answer)
        elif self.voice.enabled:
            key = "mic_error" if error in {"OSError", "AttributeError"} else "not_heard"
            self.voice.speak(tr(self.settings.language, key))
        self.listening = False
        log.info("Conversation listening finished; error=%s", error)

    def _voice_loop(self):
        wake_words = ("hey memo", "hey memocan", "memocan", "memo")
        while not self.closing:
            if self.manual_voice.is_set():
                self.manual_voice.clear(); self.listening = True
                self._conversation_worker(); continue
            if self.settings.listening_enabled and self.voice.enabled:
                heard, _ = self.voice.listen_once(timeout=0.6, phrase_time_limit=2, calibrate=0.1)
                if heard and any(word in heard.casefold() for word in wake_words):
                    self.listening = True; self._conversation_worker()
            else:
                self.manual_voice.wait(0.25)

    def _answer(self, message):
        low = message.casefold().strip()
        if low in {"su", "su içtim", "su ictim", "water", "i drank water"}:
            return tr(self.settings.language, "water", count=self.stats.add_water())
        if low in {"rapor", "report", "haftalık rapor", "weekly report"}:
            return self._report_text()
        return self.llm.chat(message, str(self.stats.weekly()))

    def _report_text(self):
        weekly = self.stats.weekly()
        return tr(self.settings.language, "report_text", hours=weekly["active_seconds"] // 3600, water=weekly["water_count"])

    def _tick(self):
        idle = idle_seconds()
        if idle < self.settings.idle_seconds:
            self.active_session += 1
            if self.settings.reminder_enabled and self.active_session >= self.settings.break_minutes * 60 and not self.reminded:
                self.reminded = True
                self.voice.alert(tr(self.settings.language, "break"))
        elif self.active_session:
            self.stats.add_active(self.active_session, idle)
            self.active_session, self.reminded = 0, False
        self.root.after(1000, self._tick)

    def _accessible_menu(self):
        log.info("Accessible menu opened")
        self.voice.speak(
            tr(self.settings.language, "menu") + ". " +
            tr(self.settings.language, "talk") + ": Kontrol Alt V. " +
            tr(self.settings.language, "settings") + ". " +
            tr(self.settings.language, "report") + ".",
            force=True, wait=False,
        )
        existing = self.root.nametowidget(".accessible") if "accessible" in self.root.children else None
        if existing:
            existing.deiconify(); existing.lift(); existing.focus_force(); return
        win = tk.Toplevel(self.root, name="accessible")
        win.title(tr(self.settings.language, "menu")); win.geometry("360x280")
        frame = ttk.Frame(win, padding=18); frame.pack(fill="both", expand=True)
        heading = ttk.Label(frame, text=tr(self.settings.language, "menu"), font=("Segoe UI", 14, "bold"))
        heading.pack(pady=(0, 12))
        talk = ttk.Button(frame, text=tr(self.settings.language, "talk") + " (Ctrl+Alt+V)", command=self._start_conversation)
        talk.pack(fill="x", pady=4)
        ttk.Button(frame, text=tr(self.settings.language, "report"), command=lambda: self.voice.alert(self._report_text())).pack(fill="x", pady=4)
        ttk.Button(frame, text=tr(self.settings.language, "settings"), command=self._settings_window).pack(fill="x", pady=4)
        ttk.Button(frame, text=tr(self.settings.language, "quit"), command=self._quit).pack(fill="x", pady=4)
        talk.focus_set()

    def _settings_window(self):
        win = tk.Toplevel(self.root); win.title(tr(self.settings.language, "settings")); win.geometry("430x500")
        frame = ttk.Frame(win, padding=16); frame.pack(fill="both", expand=True)
        language = tk.StringVar(value=self.settings.language)
        avatar = tk.StringVar(value=self.settings.avatar)
        minutes = tk.IntVar(value=self.settings.break_minutes)
        voice = tk.BooleanVar(value=self.settings.voice_enabled)
        wake = tk.BooleanVar(value=self.settings.listening_enabled)
        startup = tk.BooleanVar(value=self.settings.startup_enabled)
        microphone_names = self.voice.microphone_names()
        microphone_values = [f"{index}: {name}" for index, name in enumerate(microphone_names)]
        current_mic = self.voice.microphone_index
        microphone = tk.StringVar(value=next((v for v in microphone_values if v.startswith(f"{current_mic}:")), ""))
        ttk.Label(frame, text=tr(self.settings.language, "language")).pack(anchor="w")
        ttk.Combobox(frame, textvariable=language, values=["tr", "en"], state="readonly").pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text=tr(self.settings.language, "avatar")).pack(anchor="w")
        ttk.Combobox(frame, textvariable=avatar, values=list(AVATARS), state="readonly").pack(fill="x", pady=(0, 8))
        ttk.Label(frame, text=tr(self.settings.language, "break_minutes")).pack(anchor="w")
        ttk.Spinbox(frame, from_=5, to=180, textvariable=minutes).pack(fill="x", pady=(0, 8))
        ttk.Checkbutton(frame, text=tr(self.settings.language, "voice"), variable=voice).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text=tr(self.settings.language, "wake"), variable=wake).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text=tr(self.settings.language, "startup"), variable=startup).pack(anchor="w", pady=4)
        ttk.Label(frame, text=tr(self.settings.language, "microphone")).pack(anchor="w", pady=(8, 0))
        ttk.Combobox(frame, textvariable=microphone, values=microphone_values, state="readonly").pack(fill="x", pady=(0, 8))
        def save():
            self.settings.language, self.settings.avatar = language.get(), avatar.get()
            self.settings.break_minutes = minutes.get()
            self.settings.voice_enabled, self.settings.listening_enabled = voice.get(), wake.get()
            self.settings.startup_enabled = startup.get()
            self.settings.microphone_index = int(microphone.get().split(":", 1)[0]) if microphone.get() else -1
            self.voice.enabled, self.voice.language = voice.get(), language.get()
            self.voice.microphone_index = self.settings.microphone_index
            save_settings(self.settings)
            set_startup(self.settings.startup_enabled)
            self.canvas.delete("all"); self._draw_avatar(); win.destroy()
            self.voice.alert(tr(self.settings.language, "saved"))
        ttk.Button(frame, text=tr(self.settings.language, "save"), command=save).pack(fill="x", pady=(14, 4))
        ttk.Button(frame, text=tr(self.settings.language, "quit"), command=self._quit).pack(fill="x", pady=4)

    def _quit(self):
        self.closing = True
        if self.active_session: self.stats.add_active(self.active_session)
        self.hotkeys.stop(); self.voice.close(); self.root.destroy()

    def run(self):
        self.root.geometry("+1000+700")
        self.root.mainloop()
