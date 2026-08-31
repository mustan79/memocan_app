from __future__ import annotations
import json, os, sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    env_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    load_dotenv(env_dir / ".env")

@dataclass
class Settings:
    avatar: str = "robot"
    break_minutes: int = 25
    reminder_enabled: bool = True
    voice_enabled: bool = True
    listening_enabled: bool = True
    language: str = "tr"
    notifications_enabled: bool = True
    startup_enabled: bool = False
    microphone_index: int = -1
    provider: str = "ollama_cloud"
    model: str = "gemma4:31b-cloud"
    base_url: str = "https://ollama.com/v1"
    api_key: str = ""
    idle_seconds: int = 300

def config_dir() -> Path:
    path = Path(os.environ.get("APPDATA") or (Path.home() / ".config")) / "Memocan"
    path.mkdir(parents=True, exist_ok=True)
    return path

def load_settings() -> Settings:
    path = config_dir() / "config.json"
    if not path.exists():
        settings = Settings()
    else:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            settings = Settings(**{k: v for k, v in data.items() if k in Settings.__dataclass_fields__})
        except (OSError, ValueError, TypeError):
            settings = Settings()

    provider = os.environ.get("MEMOCAN_PROVIDER", settings.provider).strip().lower()
    providers = {
        "ollama_cloud": ("OLLAMA_API_KEY", "https://ollama.com/v1", "gemma4:31b-cloud"),
        "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "openrouter/auto"),
        "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-chat"),
    }
    if provider not in providers:
        provider = "ollama_cloud"
    if provider == "deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = os.environ.get("DEEPSEAK_API_KEY", "")
    key_name, default_url, default_model = providers.get(provider, providers["ollama_cloud"])
    settings.provider = provider
    settings.api_key = os.environ.get(key_name, settings.api_key).strip()
    settings.base_url = os.environ.get("MEMOCAN_BASE_URL", default_url).strip()
    settings.model = os.environ.get("MEMOCAN_MODEL", default_model).strip()
    return settings

def save_settings(settings: Settings) -> None:
    data = asdict(settings)
    data.pop("api_key", None)
    (config_dir() / "config.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
