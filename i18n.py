STRINGS = {
    "tr": {
        "ready": "Memocan hazır.", "listening": "Dinliyorum.", "voice_off": "Ses kapalı.",
        "not_heard": "Seni anlayamadım.", "mic_error": "Mikrofona erişemedim.",
        "menu": "Memocan erişilebilir menü", "talk": "Sesli konuş", "settings": "Ayarlar",
        "report": "Haftalık rapor", "quit": "Memocan'ı kapat", "save": "Kaydet",
        "language": "Dil", "avatar": "Avatar", "break_minutes": "Mola süresi, dakika",
        "voice": "Sesli yanıtlar", "wake": "Hey Memo ile uyanma", "notifications": "Bildirimler",
        "startup": "Oturum açınca Memocan'ı başlat",
        "microphone": "Mikrofon",
        "saved": "Ayarlar kaydedildi.", "break": "Çok oturdun. Ayağa kalkıp biraz hareket eder misin? Su içmeyi unutma.",
        "water": "Harika, bugün {count} bardak su içtin.",
        "water_total": "Bugün toplam {count} bardak su içtin.",
        "report_text": "Son 7 günde {hours} saat aktiftin ve {water} bardak su içtin.",
        "hotkey_error": "Kontrol Alt M kısayolu başka bir uygulama tarafından kullanılıyor.",
    },
    "en": {
        "ready": "Memocan is ready.", "listening": "I'm listening.", "voice_off": "Voice is off.",
        "not_heard": "I couldn't understand you.", "mic_error": "I couldn't access the microphone.",
        "menu": "Memocan accessible menu", "talk": "Voice conversation", "settings": "Settings",
        "report": "Weekly report", "quit": "Quit Memocan", "save": "Save",
        "language": "Language", "avatar": "Avatar", "break_minutes": "Break interval, minutes",
        "voice": "Spoken responses", "wake": "Wake with Hey Memo", "notifications": "Notifications",
        "startup": "Start Memocan when I sign in",
        "microphone": "Microphone",
        "saved": "Settings saved.", "break": "You have been sitting for a while. Please move and remember to drink water.",
        "water": "Great, you have had {count} glasses of water today.",
        "water_total": "You have had {count} glasses of water today.",
        "report_text": "In the last 7 days, you were active for {hours} hours and drank {water} glasses of water.",
        "hotkey_error": "Control Alt M is already used by another application.",
    },
}

def tr(language: str, key: str, **values) -> str:
    table = STRINGS.get(language, STRINGS["tr"])
    return table.get(key, STRINGS["tr"].get(key, key)).format(**values)
