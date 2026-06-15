"""Theme + language toggle bar for menus and login screen."""

from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QWidget

from language_toggle import LanguageToggle
from theme_toggle import ThemeToggle


class ViewTogglesBar(QWidget):
    """Horizontal bar with theme and language toggles."""

    def __init__(self, parent=None, *, persist: bool = True) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(8)
        self.theme_toggle = ThemeToggle(persist=persist)
        self.language_toggle = LanguageToggle(persist=persist)
        lay.addWidget(self.theme_toggle)
        lay.addWidget(self.language_toggle)
