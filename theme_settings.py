"""Application theme persistence and change notifications."""

from __future__ import annotations

import os
from configparser import ConfigParser

from PyQt5.QtCore import QObject, pyqtSignal

THEME_DARK = "dark"
THEME_LIGHT = "light"
THEMES = (THEME_DARK, THEME_LIGHT)

_CONFIG_NAME = "dev.ini"
_SECTION = "AppSettings"
_KEY = "theme"


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


def normalize_theme(name: str | None) -> str:
    if name and str(name).strip().lower() == THEME_LIGHT:
        return THEME_LIGHT
    return THEME_DARK


def get_theme() -> str:
    parser = _read_parser()
    if not parser.has_section(_SECTION) or not parser.has_option(_SECTION, _KEY):
        return THEME_DARK
    return normalize_theme(parser.get(_SECTION, _KEY))


def save_theme_to_ini(theme: str) -> None:
    theme = normalize_theme(theme)
    parser = _read_parser()
    if not parser.has_section(_SECTION):
        parser.add_section(_SECTION)
    parser.set(_SECTION, _KEY, theme)
    _write_parser(parser)


class ThemeManager(QObject):
    """Singleton-style manager: load/save theme and emit theme_changed."""

    theme_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._current = get_theme()

    @property
    def current(self) -> str:
        return self._current

    def set_theme(self, theme: str, *, persist: bool = True) -> None:
        theme = normalize_theme(theme)
        if theme == self._current and persist:
            return
        self._current = theme
        if persist:
            save_theme_to_ini(theme)
        self.theme_changed.emit(theme)

    def reload(self) -> str:
        self._current = get_theme()
        return self._current


_manager: ThemeManager | None = None


def manager() -> ThemeManager:
    global _manager
    if _manager is None:
        _manager = ThemeManager()
    return _manager
