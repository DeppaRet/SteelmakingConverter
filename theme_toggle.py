"""Moon / sun theme switch widget."""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from theme_settings import THEME_DARK, THEME_LIGHT, get_theme, manager


class ThemeToggle(QWidget):
    """Click moon (left) for dark, sun (right) for light."""

    theme_changed = pyqtSignal(str)

    TRACK_W = 76
    TRACK_H = 28
    PAD = 2

    def __init__(self, parent=None, *, persist: bool = True) -> None:
        super().__init__(parent)
        self._persist = persist
        self._light = get_theme() == THEME_LIGHT
        self._knob = 1.0 if self._light else 0.0
        self.setFixedSize(self.TRACK_W, self.TRACK_H)
        self.setCursor(Qt.PointingHandCursor)
        self._update_tooltip()

    def _update_tooltip(self) -> None:
        try:
            from i18n import tr
            self.setToolTip(tr("ThemeToggle", "Тёмная тема (луна) / Светлая тема (солнце)"))
        except ImportError:
            self.setToolTip("Тёмная тема (луна) / Светлая тема (солнце)")
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def is_light(self) -> bool:
        return self._light

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

    def set_light(self, light: bool, *, emit_manager: bool = True) -> None:
        light = bool(light)
        if light == self._light and abs(self._knob - (1.0 if light else 0.0)) < 0.01:
            return
        self._light = light
        target = 1.0 if light else 0.0
        self._anim.stop()
        self._anim.setStartValue(self._knob)
        self._anim.setEndValue(target)
        self._anim.start()
        if emit_manager:
            theme = THEME_LIGHT if light else THEME_DARK
            manager().set_theme(theme, persist=self._persist)
            self.theme_changed.emit(theme)

    def sync_from_settings(self) -> None:
        self._anim.stop()
        self._light = get_theme() == THEME_LIGHT
        self._knob = 1.0 if self._light else 0.0
        self._update_tooltip()
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        self.set_light(event.x() >= self.width() / 2)
        event.accept()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        half_w = w / 2.0
        knob = self._knob_rect()

        if self._light:
            track = QColor(214, 222, 234)
            border = QColor(0, 120, 168, 150)
            knob_col = QColor(255, 170, 40)
            inactive_icon = QColor(120, 132, 152)
            active_icon = QColor(255, 255, 255)
            active_glyph = "\u2600"
            inactive_glyph = "\u263E"
            inactive_rect = QRectF(0, 0, half_w, h)
        else:
            track = QColor(28, 32, 48)
            border = QColor(0, 200, 240, 110)
            knob_col = QColor(0, 200, 240)
            inactive_icon = QColor(100, 110, 130)
            active_icon = QColor(255, 255, 255)
            active_glyph = "\u263E"
            inactive_glyph = "\u2600"
            inactive_rect = QRectF(half_w, 0, half_w, h)

        radius = h / 2.0
        p.setPen(QPen(border, 1))
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), radius, radius)

        icon_font = QFont("Segoe UI Symbol", 13, QFont.Bold)
        p.setFont(icon_font)

        p.setPen(inactive_icon)
        p.drawText(inactive_rect, Qt.AlignCenter, inactive_glyph)

        p.setPen(Qt.NoPen)
        p.setBrush(knob_col)
        p.drawEllipse(knob)

        p.setPen(active_icon)
        p.drawText(knob, Qt.AlignCenter, active_glyph)
