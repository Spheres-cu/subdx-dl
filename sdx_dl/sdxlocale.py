# Copyright (C) 2025 Spheres-cu (https://github.com/Spheres-cu) subdx-dl
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from importlib.resources import files
from typing import Dict, Optional, Any, Set
from locale import getlocale
from sdx_dl.sdxconsole import console
import json
import sys

local_language = f"{getlocale()[0]}".split('_')[0] if getlocale()[0] else ""

__all__ = ['Translator', 'set_locale', 'get_locale', 'gl']

class Translator:
    def __init__(self, locale: str = local_language):
        """
        Initialize the translator with a default locale.
        
        Args:
            locale: Default language code ('es', 'en')
        """
        self.locale = locale if files('sdx_dl.language').joinpath(f"{locale}.json").is_file() else "en"
        self._translations: Dict[str, Dict[str, str]] = {}
        self._loaded_locales:Set[str] = set()

    def load_translations(self, locale: str) -> None:
        """
        Load translations for a specific locale if not already loaded.
        
        Args:
            locale: Language code to load
        """
        if locale in self._loaded_locales:
            return
        
        if files('sdx_dl.language').joinpath(f"{self.locale}.json").is_file():
            data_file = files('sdx_dl.language').joinpath(f"{self.locale}.json").open(mode='r', encoding='utf-8')
            try: 
                self._translations[locale] = json.load(data_file)
                self._loaded_locales.add(locale)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in translation file for locale: {locale}")
        else:
            console.print(":no_entry: [bold red] Don't exists a language file!")
            sys.exit(1)

    def set_locale(self, locale: str) -> None:
        """
        Set the current locale and load its translations if not already loaded.
        
        Args:
            locale: Language code to set as current
        """
        self.locale = locale
        self.load_translations(locale)

    def translate(self, key: str, locale: Optional[str] = None, **kwargs: Any) -> str:
        """
        Translate a string key to the specified or current locale.
        
        Args:
            key: Translation key
            locale: Optional language code (uses current locale if None)
            **kwargs: Formatting arguments for the translated string
            
        Returns:
            Translated string, or the key if translation not found
        """
        locale = locale or self.locale
        if locale not in self._loaded_locales:
            self.load_translations(locale)
            
        translations = self._translations.get(locale, {})
        translated = translations.get(key, key)
        
        if kwargs:
            try:
                return translated.format(**kwargs)
            except (KeyError, ValueError):
                return translated
        return translated


# Singleton instance for easy access
translator = Translator()

def set_locale(locale: str) -> None:
    """Set the locale for the default translator instance."""
    translator.set_locale(locale)

def get_locale(key: str, **kwargs: Any) -> str:
    """Translate a key using the default translator instance."""
    return translator.translate(key, **kwargs)

# Alias for get_locale
gl = get_locale