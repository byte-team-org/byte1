import json
import os
from typing import Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")

_cache: dict[str, dict] = {}


def load_locale(lang: str) -> dict:
    if lang not in _cache:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.exists(path):
            path = os.path.join(LOCALES_DIR, "ru.json")
        with open(path, encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Translate a key into the given language with optional formatting."""
    locale = load_locale(lang)
    text = locale.get(key, load_locale("ru").get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


class I18nMiddleware(BaseMiddleware):
    """Middleware that injects the user's language into handler data."""

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]):
        # Try to get language from FSM state data
        lang = "ru"
        state = data.get("state")
        if state:
            try:
                state_data = await state.get_data()
                lang = state_data.get("language", "ru")
            except Exception:
                pass
        data["lang"] = lang
        data["t"] = lambda key, **kw: t(key, lang, **kw)
        return await handler(event, data)
