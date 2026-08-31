from __future__ import annotations
import os
import platform
import shlex
import sys
from pathlib import Path

def _command():
    if getattr(sys, "frozen", False): return [str(Path(sys.executable).resolve())]
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    executable = pythonw if pythonw.exists() else Path(sys.executable)
    return [str(executable.resolve()), str(Path(__file__).with_name("main.py").resolve())]

def set_startup(enabled: bool):
    system, command = platform.system(), _command()
    if system == "Windows":
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            if enabled:
                winreg.SetValueEx(key, "Memocan", 0, winreg.REG_SZ, " ".join(f'"{part}"' for part in command))
            else:
                try: winreg.DeleteValue(key, "Memocan")
                except FileNotFoundError: pass
    elif system == "Darwin":
        path = Path.home() / "Library/LaunchAgents/com.memocan.app.plist"
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            args = "".join(f"<string>{part}</string>" for part in command)
            path.write_text(f'<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>Label</key><string>com.memocan.app</string><key>ProgramArguments</key><array>{args}</array><key>RunAtLoad</key><true/></dict></plist>', encoding="utf-8")
        else:
            path.unlink(missing_ok=True)
    else:
        path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart/memocan.desktop"
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            cmd = " ".join(shlex.quote(part) for part in command)
            path.write_text(f"[Desktop Entry]\nType=Application\nName=Memocan\nExec={cmd}\nX-GNOME-Autostart-enabled=true\n", encoding="utf-8")
        else:
            path.unlink(missing_ok=True)
