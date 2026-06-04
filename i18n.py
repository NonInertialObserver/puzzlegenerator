import json
import locale
import os
from typing import Any, Dict


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "中文",
}
LOCALE_FILE = os.path.join(os.path.dirname(__file__), "locale", "lp.json")


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    language = language.lower().replace("_", "-")
    base_language = language.split("-", 1)[0]
    if base_language in SUPPORTED_LANGUAGES:
        return base_language
    return DEFAULT_LANGUAGE


def load_translations() -> Dict[str, Dict[str, str]]:
    with open(LOCALE_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"translation file must contain a language mapping: {LOCALE_FILE}")

    translations: Dict[str, Dict[str, str]] = {}
    for language, messages in data.items():
        if isinstance(messages, dict):
            translations[normalize_language(language)] = {
                str(key): str(value) for key, value in messages.items()
            }
    return translations


TRANSLATIONS = load_translations()


def detect_language() -> str:
    env_language = os.getenv("PUZZLEGEN_LANG") or os.getenv("LANGUAGE") or os.getenv("LANG")
    if env_language:
        return normalize_language(env_language.split(":", 1)[0])

    locale_language, _ = locale.getlocale()
    return normalize_language(locale_language)


class Translator:
    def __init__(self, language: str | None = None) -> None:
        self.language = normalize_language(language or detect_language())

    def set_language(self, language: str) -> None:
        self.language = normalize_language(language)

    def gettext(self, key: str, **kwargs: Any) -> str:
        template = TRANSLATIONS.get(self.language, {}).get(key)
        if template is None:
            template = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
        return template.format(**kwargs) if kwargs else template


def get_language_display_name(language: str) -> str:
    return SUPPORTED_LANGUAGES[normalize_language(language)]


def language_from_display_name(display_name: str) -> str:
    for language, name in SUPPORTED_LANGUAGES.items():
        if name == display_name:
            return language
    return normalize_language(display_name)