from __future__ import annotations
import ctypes, logging, re, threading
import wx
from autostart import set_startup
from config import load_settings, save_settings
from hotkeys import HotkeyManager
from i18n import tr
from llm import LLMClient
from storage import StatsStore
from tracker import WorkTimer
from voice import Voice

log = logging.getLogger("memocan.app")
AVATARS = {"robot": "🤖", "cat": "🐱", "owl": "🦉", "duck": "🦆"}

class ButtonAccessible(wx.Accessible):
    def __init__(self, button): super().__init__(button); self.button = button
    def GetName(self, child_id): return wx.ACC_OK, self.button.GetLabel()
    def GetRole(self, child_id): return wx.ACC_OK, wx.ROLE_SYSTEM_PUSHBUTTON
    def GetDefaultAction(self, child_id): return wx.ACC_OK, "Bas"
    def GetState(self, child_id):
        state = wx.ACC_STATE_SYSTEM_FOCUSABLE
        if self.button.HasFocus(): state |= wx.ACC_STATE_SYSTEM_FOCUSED
        if not self.button.IsEnabled(): state |= wx.ACC_STATE_SYSTEM_UNAVAILABLE
        return wx.ACC_OK, state

def make_accessible(button):
    accessible = ButtonAccessible(button); button.SetAccessible(accessible); button._memocan_accessible = accessible
    button.Bind(wx.EVT_SET_FOCUS, lambda event: (wx.Accessible.NotifyEvent(wx.ACC_EVENT_OBJECT_FOCUS, button, wx.OBJID_CLIENT, wx.ACC_SELF), event.Skip()))
    return button

def idle_seconds() -> int:
    if not hasattr(ctypes, "windll"): return 0
    class LASTINPUTINFO(ctypes.Structure): _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO(ctypes.sizeof(LASTINPUTINFO), 0)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)): return max(0, (ctypes.windll.kernel32.GetTickCount() - info.dwTime) // 1000)
    return 0

class MemocanApp:
    def __init__(self):
        self.settings, self.stats = load_settings(), StatsStore(); self.llm = LLMClient(self.settings)
        self.voice = Voice(self.settings.voice_enabled, self.settings.language, self.settings.microphone_index)
        self.listening, self.closing, self.active_session, self.reminded = False, False, 0, False
        self.work_timer = WorkTimer(self.settings.break_minutes)
        self.manual_voice = threading.Event(); self.wx_app = wx.App(False)
        self.frame = wx.Frame(None, title="Memocan", size=(120, 120), style=wx.FRAME_NO_TASKBAR | wx.STAY_ON_TOP | wx.BORDER_NONE)
        panel = wx.Panel(self.frame); panel.SetBackgroundColour("#4f8cff")
        self.avatar_button = wx.Button(panel, label=AVATARS.get(self.settings.avatar, "🤖"), pos=(8, 8), size=(104, 104), name="Memocan")
        make_accessible(self.avatar_button)
        font = self.avatar_button.GetFont(); font.SetPointSize(36); self.avatar_button.SetFont(font); self.avatar_button.SetToolTip("Memocan - Ctrl+Alt+M")
        self.avatar_button.Bind(wx.EVT_BUTTON, lambda _: self._accessible_menu()); self.avatar_button.Bind(wx.EVT_RIGHT_DOWN, lambda _: self._settings_window())
        self.frame.SetPosition((1000, 700)); self.frame.Show(); self.menu_frame = None
        self.timer = wx.Timer(self.frame); self.frame.Bind(wx.EVT_TIMER, self._tick, self.timer); self.timer.Start(1000)
        self.hotkeys = HotkeyManager({"menu": lambda: wx.CallAfter(self._accessible_menu), "voice": lambda: wx.CallAfter(self._voice_hotkey)})
        if "menu" in self.hotkeys.start(): threading.Thread(target=lambda: self.voice.alert(tr(self.settings.language, "hotkey_error")), daemon=True).start()
        threading.Thread(target=self._voice_loop, daemon=True, name="memocan-listener").start()

    def _voice_hotkey(self):
        log.info("Voice hotkey activated; listening=%s enabled=%s", self.listening, self.voice.enabled)
        if self.listening:
            self.voice.enabled = False; self.settings.voice_enabled = False; save_settings(self.settings); self.manual_voice.clear()
            self.voice.speak(tr(self.settings.language, "voice_off"), force=True, wait=False); return
        if not self.voice.enabled: self.voice.enabled = True; self.settings.voice_enabled = True; save_settings(self.settings)
        self.manual_voice.set(); self.voice.beep()

    def _start_conversation(self):
        if not self.closing: self.manual_voice.set()

    def _conversation_worker(self):
        log.info("Conversation listening started"); self.voice.speak(tr(self.settings.language, "listening"), force=True)
        heard, error = self.voice.listen_once()
        if heard and self.voice.enabled: self.voice.speak(self._answer(heard))
        elif self.voice.enabled: self.voice.speak(tr(self.settings.language, "mic_error" if error in {"OSError", "AttributeError"} else "not_heard"))
        self.listening = False; log.info("Conversation listening finished; error=%s", error)

    def _voice_loop(self):
        wake_words = ("hey memo", "hey memocan", "memocan", "memo")
        while not self.closing:
            if self.manual_voice.is_set(): self.manual_voice.clear(); self.listening = True; self._conversation_worker(); continue
            if self.settings.listening_enabled and self.voice.enabled:
                heard, _ = self.voice.listen_once(timeout=0.6, phrase_time_limit=2, calibrate=0.1)
                if heard and any(word in heard.casefold() for word in wake_words): self.listening = True; self._conversation_worker()
            else: self.manual_voice.wait(0.25)

    def _answer(self, message):
        low = message.casefold().strip()
        history = self.stats.recent_conversation(12)
        number_words = {"bir": 1, "iki": 2, "üç": 3, "uc": 3, "dört": 4, "dort": 4, "beş": 5, "bes": 5,
                        "altı": 6, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9, "on": 10}
        water_query = re.search(r"(kaç|ne kadar).*(su|bardak)|(su|bardak).*(kaç|ne kadar)", low)
        water_log = re.search(r"(?:(\d+|bir|iki|üç|uc|dört|dort|beş|bes|altı|alti|yedi|sekiz|dokuz|on)\s*)?(?:bardak|şişe|sise)?\s*su\s*(?:içtim|ictim|içiyorum|içerim|drank)", low)
        if water_query:
            answer = tr(self.settings.language, "water_total", count=self.stats.today_water())
        elif water_log:
            raw = water_log.group(1); count = int(raw) if raw and raw.isdigit() else number_words.get(raw or "bir", 1)
            answer = tr(self.settings.language, "water", count=self.stats.add_water(count))
        elif low in {"rapor", "report", "haftalık rapor", "weekly report"}:
            answer = self._report_text()
        else:
            answer = self.llm.chat(message, history)
        self.stats.add_conversation("user", message); self.stats.add_conversation("assistant", answer)
        return answer

    def _report_text(self):
        weekly = self.stats.weekly(); return tr(self.settings.language, "report_text", hours=weekly["active_seconds"] // 3600, water=weekly["water_count"])

    def _tick(self, _event=None):
        idle = idle_seconds()
        active = idle < self.settings.idle_seconds
        if active:
            self.active_session += 1
            if self.settings.reminder_enabled and self.work_timer.advance(True):
                log.info("Break reminder triggered after %s active seconds", self.work_timer.threshold)
                threading.Thread(target=lambda: self.voice.alert(tr(self.settings.language, "break")), daemon=True).start()
        elif self.active_session: self.stats.add_active(self.active_session, idle); self.active_session, self.reminded = 0, False

    def _accessible_menu(self):
        if self.menu_frame and self.menu_frame.IsShown(): self.menu_frame.Hide(); return
        log.info("Accessible menu opened"); self.voice.speak(tr(self.settings.language, "menu"), force=True, wait=False)
        if self.menu_frame: self.menu_frame.Show(); self.menu_frame.Raise(); self.menu_buttons[0].SetFocus(); return
        frame = wx.Frame(self.frame, title=tr(self.settings.language, "menu"), size=(500, 420), style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        panel = wx.Panel(frame); layout = wx.BoxSizer(wx.VERTICAL); heading = wx.StaticText(panel, label=tr(self.settings.language, "menu"))
        font = heading.GetFont(); font.SetPointSize(15); font.SetWeight(wx.FONTWEIGHT_BOLD); heading.SetFont(font); layout.Add(heading, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 18)
        specs = [(tr(self.settings.language, "talk") + " (Ctrl+Alt+V)", self._start_conversation),
                 (tr(self.settings.language, "report"), lambda: threading.Thread(target=lambda: self.voice.alert(self._report_text()), daemon=True).start()),
                 (tr(self.settings.language, "settings"), self._settings_window), (tr(self.settings.language, "quit"), self._quit)]
        self.menu_buttons = []
        for label, callback in specs:
            button = wx.Button(panel, label=label, size=(-1, 50), name=label); button.SetToolTip(label)
            button.Bind(wx.EVT_BUTTON, lambda event, cb=callback: (self.menu_frame.Hide(), cb()))
            make_accessible(button)
            layout.Add(button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 18); self.menu_buttons.append(button)
        panel.SetSizer(layout); frame.Bind(wx.EVT_CLOSE, lambda event: frame.Hide()); self.menu_frame = frame; frame.Show(); frame.Raise(); self.menu_buttons[0].SetFocus()

    def _settings_window(self):
        dialog = wx.Dialog(self.frame, title=tr(self.settings.language, "settings"), size=(520, 620)); panel = wx.Panel(dialog); layout = wx.BoxSizer(wx.VERTICAL)
        def label(text): layout.Add(wx.StaticText(panel, label=text), 0, wx.LEFT | wx.RIGHT | wx.TOP, 14)
        label(tr(self.settings.language, "language")); language = wx.Choice(panel, choices=["tr", "en"]); language.SetStringSelection(self.settings.language); layout.Add(language, 0, wx.EXPAND | wx.ALL, 8)
        label(tr(self.settings.language, "avatar")); avatar = wx.Choice(panel, choices=list(AVATARS)); avatar.SetStringSelection(self.settings.avatar); layout.Add(avatar, 0, wx.EXPAND | wx.ALL, 8)
        label(tr(self.settings.language, "break_minutes")); minutes = wx.SpinCtrl(panel, min=5, max=180, initial=self.settings.break_minutes); layout.Add(minutes, 0, wx.EXPAND | wx.ALL, 8)
        voice = wx.CheckBox(panel, label=tr(self.settings.language, "voice")); voice.SetValue(self.settings.voice_enabled); layout.Add(voice, 0, wx.ALL, 8)
        wake = wx.CheckBox(panel, label=tr(self.settings.language, "wake")); wake.SetValue(self.settings.listening_enabled); layout.Add(wake, 0, wx.ALL, 8)
        startup = wx.CheckBox(panel, label=tr(self.settings.language, "startup")); startup.SetValue(self.settings.startup_enabled); layout.Add(startup, 0, wx.ALL, 8)
        names = self.voice.microphone_names(); label(tr(self.settings.language, "microphone")); microphone = wx.Choice(panel, choices=[f"{i}: {n}" for i, n in enumerate(names)]); microphone.SetSelection(max(0, self.voice.microphone_index)); layout.Add(microphone, 0, wx.EXPAND | wx.ALL, 8)
        save = wx.Button(panel, label=tr(self.settings.language, "save"), name=tr(self.settings.language, "save")); layout.Add(save, 0, wx.EXPAND | wx.ALL, 12)
        make_accessible(save)
        def do_save(_):
            self.settings.language, self.settings.avatar = language.GetStringSelection(), avatar.GetStringSelection(); self.settings.break_minutes = minutes.GetValue()
            self.settings.voice_enabled, self.settings.listening_enabled, self.settings.startup_enabled = voice.GetValue(), wake.GetValue(), startup.GetValue(); self.settings.microphone_index = microphone.GetSelection()
            self.work_timer.set_minutes(self.settings.break_minutes)
            self.voice.enabled, self.voice.language, self.voice.microphone_index = self.settings.voice_enabled, self.settings.language, self.settings.microphone_index
            self.avatar_button.SetLabel(AVATARS.get(self.settings.avatar, "🤖")); save_settings(self.settings); set_startup(self.settings.startup_enabled); dialog.EndModal(wx.ID_OK)
            threading.Thread(target=lambda: self.voice.alert(tr(self.settings.language, "saved")), daemon=True).start()
        save.Bind(wx.EVT_BUTTON, do_save); panel.SetSizer(layout); dialog.ShowModal(); dialog.Destroy()

    def _quit(self):
        self.closing = True; self.timer.Stop()
        if self.active_session: self.stats.add_active(self.active_session)
        self.hotkeys.stop(); self.voice.close()
        if self.menu_frame: self.menu_frame.Destroy()
        self.frame.Destroy(); self.wx_app.ExitMainLoop()

    def run(self): self.wx_app.MainLoop()
