"""RU / EN language switch widget."""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from locale_settings import LANG_EN, LANG_RU, get_language, manager


class LanguageToggle(QWidget):
    """Click RU (left) for Russian, EN (right) for English."""

    language_changed = pyqtSignal(str)

    TRACK_W = 76
    TRACK_H = 28
    PAD = 2

    def __init__(self, parent=None, *, persist: bool = True) -> None:
        super().__init__(parent)
        self._persist = persist
        self._english = get_language() == LANG_EN
        self._knob = 1.0 if self._english else 0.0
        self.setFixedSize(self.TRACK_W, self.TRACK_H)
        self.setCursor(Qt.PointingHandCursor)
        self._update_tooltip()
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _update_tooltip(self) -> None:
        try:
            from i18n import tr
            self.setToolTip(tr("LanguageToggle", "Русский (RU) / English (EN)"))
        except ImportError:
            self.setToolTip("Русский (RU) / English (EN)")

    def is_english(self) -> bool:
        return self._english

    def get_knob_pos(self) -> float:
        return self._knob

    def set_knob_pos(self, value: float) -> None:
        self._knob = max(0.0, min(1.0, value))
        self.update()

    knobPos = pyqtProperty(float, get_knob_pos, set_knob_pos)

    def _knob_rect(self) -> QRectF:
        w, h = float(self.width()), float(self.height())
        pad = float(self.PAD)
        knob = h - 2 * pad
        inner = w - 2 * pad
        half = inner / 2.0
        left_x = pad + (half - knob) / 2.0
        right_x = pad + half + (half - knob) / 2.0
        x = left_x + self._knob * (right_x - left_x)
        return QRectF(x, pad, knob, knob)

    def set_english(self, english: bool, *, emit_manager: bool = True) -> None:
        english = bool(english)
        if english == self._english and abs(self._knob - (1.0 if english else 0.0)) < 0.01:
            return
        self._english = english
        target = 1.0 if english else 0.0
        self._anim.stop()
        self._anim.setStartValue(self._knob)
        self._anim.setEndValue(target)
        self._anim.start()
        if emit_manager:
            lang = LANG_EN if english else LANG_RU
            manager().set_language(lang, persist=self._persist)
            self.language_changed.emit(lang)

    def sync_from_settings(self) -> None:
        self._anim.stop()
        self._english = get_language() == LANG_EN
        self._knob = 1.0 if self._english else 0.0
        self._update_tooltip()
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        self.set_english(event.x() >= self.width() / 2)
        event.accept()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        half_w = w / 2.0
        knob = self._knob_rect()

        track = QColor(28, 32, 48)
        border = QColor(0, 200, 240, 110)
        knob_col = QColor(0, 160, 200)
        inactive_text = QColor(100, 110, 130)
        active_text = QColor(255, 255, 255)

        radius = h / 2.0
        p.setPen(QPen(border, 1))
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), radius, radius)

        label_font = QFont("Segoe UI", 9, QFont.Bold)
        p.setFont(label_font)

        inactive_rect = QRectF(0, 0, half_w, h) if self._english else QRectF(half_w, 0, half_w, h)
        p.setPen(inactive_text)
        p.drawText(inactive_rect, Qt.AlignCenter, "RU" if self._english else "EN")

        p.setPen(Qt.NoPen)
        p.setBrush(knob_col)
        p.drawEllipse(knob)

        p.setPen(active_text)
        p.drawText(knob, Qt.AlignCenter, "EN" if self._english else "RU")
