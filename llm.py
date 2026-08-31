from __future__ import annotations
import re

def clean_for_speech(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " Kod bölümü atlandı. ", text or "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~>|]", "", text)
    return re.sub(r"\s+", " ", text).strip()

class LLMClient:
    def __init__(self, settings): self.settings = settings
    def chat(self, message: str, history: list[dict] | None = None) -> str:
        try:
            from openai import OpenAI
            if not self.settings.api_key:
                return "API anahtarı ayarlanmamış. Ayarlardan bir anahtar ekleyebilirsin."
            client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url.rstrip("/"), timeout=30.0)
            system = (
                "You are Memocan. Give short, warm English answers that support healthy work habits. Never use Markdown, lists, links, emoji, stage directions, or meta commentary."
                if self.settings.language == "en" else
                "Sen Memocan'sın. Kısa, sıcak, doğal Türkçe cevaplar ver. Sağlıklı çalışma alışkanlıklarını destekle. Markdown, liste işareti, bağlantı, emoji, sahne yönergesi veya üst anlatım kullanma."
            )
            messages = [{"role":"system","content":system}] + (history or []) + [{"role":"user","content":message}]
            result = client.chat.completions.create(model=self.settings.model, messages=messages, max_tokens=250)
            return clean_for_speech(result.choices[0].message.content or ("I'm here." if self.settings.language == "en" else "Buradayım."))
        except Exception as exc:
            return (f"LLM connection failed: {exc}" if self.settings.language == "en" else f"LLM bağlantısı kurulamadı: {exc}")
