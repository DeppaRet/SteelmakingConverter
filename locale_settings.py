"""Application locale persistence and change notifications."""

from __future__ import annotations

import os
from configparser import ConfigParser

from PyQt5.QtCore import QObject, pyqtSignal

LANG_RU = "ru"
LANG_EN = "en"
LANGUAGES = (LANG_RU, LANG_EN)

_CONFIG_NAME = "dev.ini"
_SECTION = "AppSettings"
_KEY = "language"


def _config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _CONFIG_NAME)


def _read_parser() -> ConfigParser:
    parser = ConfigParser()
    path = _config_path()
    if os.path.isfile(path):
        parser.read(path, encoding="utf-8")
    return parser


def _write_parser(parser: ConfigParser) -> None:
    with open(_config_path(), "w", encoding="utf-8") as f:
        parser.write(f)


def normalize_language(name: str | None) -> str:
    if name and str(name).strip().lower() in (LANG_EN, "english", "en-us", "en_gb"):
        return LANG_EN
    return LANG_RU


def get_language() -> str:
    parser = _read_parser()
    if not parser.has_section(_SECTION) or not parser.has_option(_SECTION, _KEY):
        return LANG_RU
    return normalize_language(parser.get(_SECTION, _KEY))


def save_language_to_ini(language: str) -> None:
    language = normalize_language(language)
    parser = _read_parser()
    if not parser.has_section(_SECTION):
        parser.add_section(_SECTION)
    parser.set(_SECTION, _KEY, language)
    _write_parser(parser)


class LocaleManager(QObject):
    """Singleton-style manager: load/save language and emit language_changed."""

    language_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._current = get_language()

    @property
    def current(self) -> str:
        return self._current

    def set_language(self, language: str, *, persist: bool = True) -> None:
        language = normalize_language(language)
        if language == self._current and persist:
            return
        self._current = language
        if persist:
            save_language_to_ini(language)
        self.language_changed.emit(language)

    def reload(self) -> str:
        self._current = get_language()
        return self._current


_manager: LocaleManager | None = None


def manager() -> LocaleManager:
    global _manager
    if _manager is None:
        _manager = LocaleManager()
    return _manager
