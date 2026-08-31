from __future__ import annotations

class LLMClient:
    def __init__(self, settings): self.settings = settings
    def chat(self, message: str, context: str = "") -> str:
        try:
            from openai import OpenAI
            if not self.settings.api_key:
                return "API anahtarı ayarlanmamış. Ayarlardan bir anahtar ekleyebilirsin."
            client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url.rstrip("/"), timeout=30.0)
            system = (
                "You are Memocan. Give short, warm English answers that support healthy work habits."
                if self.settings.language == "en" else
                "Sen Memocan'sın. Kısa, sıcak, Türkçe ve sağlıklı çalışma alışkanlıklarını destekleyen cevaplar ver."
            )
            result = client.chat.completions.create(model=self.settings.model, messages=[{"role":"system","content":system}, {"role":"user","content":message}], max_tokens=250)
            return result.choices[0].message.content or ("I'm here." if self.settings.language == "en" else "Buradayım.")
        except Exception as exc:
            return (f"LLM connection failed: {exc}" if self.settings.language == "en" else f"LLM bağlantısı kurulamadı: {exc}")
