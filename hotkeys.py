from __future__ import annotations
import ctypes
import ctypes.wintypes
import platform
import threading

class HotkeyManager:
    def __init__(self, callbacks):
        self.callbacks, self.listener = callbacks, None
        self.ready, self.errors = threading.Event(), []

    def start(self):
        if platform.system() == "Windows":
            threading.Thread(target=self._windows_loop, daemon=True).start()
            self.ready.wait(2)
        else:
            try:
                from pynput import keyboard
                self.listener = keyboard.GlobalHotKeys({
                    "<ctrl>+<alt>+m": self.callbacks["menu"],
                    "<ctrl>+<alt>+v": self.callbacks["voice"],
                })
                self.listener.start()
            except Exception as exc:
                self.errors.append(str(exc))
        return self.errors

    def _windows_loop(self):
        user32 = ctypes.windll.user32
        modifiers = 0x0001 | 0x0002 | 0x4000
        active = []
        for hotkey_id, key, name in [(1, ord("M"), "menu"), (2, ord("V"), "voice")]:
            if user32.RegisterHotKey(None, hotkey_id, modifiers, key):
                active.append(hotkey_id)
            else:
                self.errors.append(name)
        self.ready.set()
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:
                callback = self.callbacks.get("menu" if msg.wParam == 1 else "voice")
                if callback: callback()
        for hotkey_id in active:
            user32.UnregisterHotKey(None, hotkey_id)

    def stop(self):
        if self.listener: self.listener.stop()
