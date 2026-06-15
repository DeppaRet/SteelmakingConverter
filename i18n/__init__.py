"""Application internationalization (RU source, EN translations)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from PyQt5.QtWidgets import QMessageBox, QWidget

from locale_settings import LANG_EN, LANG_RU, get_language, manager as locale_manager

_TRANSLATIONS: dict[str, str] | None = None
_MISSING: set[str] = set()
_DEBUG = os.environ.get("I18N_DEBUG", "").strip().lower() in ("1", "true", "yes")


def _translations_path() -> Path:
    return Path(__file__).resolve().parent / "translations_en.json"


def _load_translations() -> dict[str, str]:
    global _TRANSLATIONS
    if _TRANSLATIONS is not None:
        return _TRANSLATIONS
    path = _translations_path()
    if path.is_file():
        with open(path, encoding="utf-8") as f:
            _TRANSLATIONS = json.load(f)
    else:
        _TRANSLATIONS = {}
    return _TRANSLATIONS


def reload_translations() -> None:
    global _TRANSLATIONS
    _TRANSLATIONS = None
    _load_translations()


def canonical_label(text: str) -> str:
    """Map a UI label or its translation back to the Russian source key."""
    table = _load_translations()
    if text in table:
        return text
    for ru, en in table.items():
        if en == text:
            return ru
    return text


def tr(context: str, text: str) -> str:
    """Translate *text* for current locale. *context* mirrors Qt convention."""
    del context  # reserved for disambiguation / future use
    if get_language() != LANG_EN:
        return text
    table = _load_translations()
    translated = table.get(text)
    if translated is None:
        if _DEBUG:
            _MISSING.add(text)
        return text
    return translated


def missing_translations() -> set[str]:
    return set(_MISSING)


def install_locale(app, language: str | None = None) -> str:
    """Set application language and emit language_changed if changed."""
    lang = language if language is not None else get_language()
    locale_manager().set_language(lang, persist=False)
    return lang


def msg_critical(
    parent: QWidget | None,
    title: str,
    text: str,
    informative: str = "",
) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(tr("Message", title))
    box.setText(tr("Message", text))
    if informative:
        box.setInformativeText(tr("Message", informative))
    box.exec_()


def msg_warning(
    parent: QWidget | None,
    title: str,
    text: str,
    informative: str = "",
) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(tr("Message", title))
    box.setText(tr("Message", text))
    if informative:
        box.setInformativeText(tr("Message", informative))
    box.exec_()


def msg_info(
    parent: QWidget | None,
    title: str,
    text: str,
    informative: str = "",
) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(tr("Message", title))
    box.setText(tr("Message", text))
    if informative:
        box.setInformativeText(tr("Message", informative))
    box.exec_()


def msg_question(
    parent: QWidget | None,
    title: str,
    text: str,
    informative: str = "",
) -> int:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(tr("Message", title))
    box.setText(tr("Message", text))
    if informative:
        box.setInformativeText(tr("Message", informative))
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    return box.exec_()
