# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.compat import is_darwin
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=["pyttsx3.drivers.sapi5", "speech_recognition", "pyaudio", "pynput"],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="Memocan", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None,
)
if is_darwin:
    app = BUNDLE(exe, name="Memocan.app", bundle_identifier="com.memocan.app")
