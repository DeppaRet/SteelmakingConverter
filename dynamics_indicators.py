"""Индикаторы динамики: η·Z, риск выбросов Φ, невязка по углероду."""

from __future__ import annotations

from typing import Any

from PyQt5 import QtCore, QtWidgets

import app_theme
from melt_dynamics import CALIB_DEFAULTS
from theme_settings import get_theme
from i18n import tr


class DynamicsIndicatorsPanel(QtWidgets.QWidget):
    """Индикаторы по последнему снимку симуляции."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        compact: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dynamics_indicators_panel")
        self._compact = compact
        self._target_c = 0.12
        self._theme = get_theme()

        if compact:
            self._build_compact()
        else:
            self._build_full()
        self.set_theme(self._theme)

    def _build_compact(self) -> None:
        self.setFixedHeight(52)
        self.setMaximumWidth(340)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(12)

        self._eff_value = QtWidgets.QLabel("η·Z —")
        self._eff_value.setProperty("class", "control_knob_value")
        lay.addWidget(self._eff_value)

        self._phi_light = QtWidgets.QLabel()
        self._phi_light.setFixedSize(14, 14)
        lay.addWidget(self._phi_light)
        self._phi_text = QtWidgets.QLabel("Φ —")
        self._phi_text.setProperty("class", "control_info_hint")
        lay.addWidget(self._phi_text)

        self._dc_value = QtWidgets.QLabel("Δ[C] —")
        self._dc_value.setProperty("class", "control_info_hint")
        lay.addWidget(self._dc_value, 1)

        self._eff_bar = None
        self._eff_hint = None
        self._foam_text = None
        self._dc_hint = None

    def _build_full(self) -> None:
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 4)
        root.setSpacing(8)

        eff_box = QtWidgets.QGroupBox()
        self._eff_box = eff_box
        eff_lay = QtWidgets.QVBoxLayout(eff_box)
        self._eff_value = QtWidgets.QLabel("—")
        self._eff_value.setAlignment(QtCore.Qt.AlignCenter)
        self._eff_bar = QtWidgets.QProgressBar()
        self._eff_bar.setRange(0, 50)
        self._eff_bar.setTextVisible(False)
        self._eff_bar.setFixedHeight(10)
        self._eff_hint = QtWidgets.QLabel("оптимум h_c: 1.8–2.5 м")
        self._eff_hint.setProperty("class", "control_info_hint")
        self._eff_hint.setAlignment(QtCore.Qt.AlignCenter)
        eff_lay.addWidget(self._eff_value)
        eff_lay.addWidget(self._eff_bar)
        eff_lay.addWidget(self._eff_hint)
        root.addWidget(eff_box, 1)

        phi_box = QtWidgets.QGroupBox()
        self._phi_box = phi_box
        phi_lay = QtWidgets.QVBoxLayout(phi_box)
        phi_row = QtWidgets.QHBoxLayout()
        self._phi_light = QtWidgets.QLabel()
        self._phi_light.setFixedSize(28, 28)
        self._phi_text = QtWidgets.QLabel("Φ = —")
        self._foam_text = QtWidgets.QLabel("Δh = — м")
        self._foam_text.setProperty("class", "control_info_hint")
        phi_row.addWidget(self._phi_light)
        phi_col = QtWidgets.QVBoxLayout()
        phi_col.addWidget(self._phi_text)
        phi_col.addWidget(self._foam_text)
        phi_row.addLayout(phi_col, 1)
        phi_lay.addLayout(phi_row)
        root.addWidget(phi_box, 1)

        dc_box = QtWidgets.QGroupBox()
        self._dc_box = dc_box
        dc_lay = QtWidgets.QVBoxLayout(dc_box)
        self._dc_value = QtWidgets.QLabel("Δ[C] = —")
        self._dc_hint = QtWidgets.QLabel("")
        self._dc_hint.setWordWrap(True)
        self._dc_hint.setProperty("class", "control_info_hint")
        dc_lay.addWidget(self._dc_value)
        dc_lay.addWidget(self._dc_hint)
        root.addWidget(dc_box, 1)

    def refresh_language(self) -> None:
        if hasattr(self, "_eff_box"):
            self._eff_box.setTitle(tr("DynamicsIndicators", "Эффективность дожигания"))
        if hasattr(self, "_phi_box"):
            self._phi_box.setTitle(tr("DynamicsIndicators", "Риск выбросов Φ"))
        if hasattr(self, "_dc_box"):
            self._dc_box.setTitle(tr("DynamicsIndicators", "Невязка по углероду"))
        if self._eff_hint is not None:
            self._eff_hint.setText(tr("DynamicsIndicators", "оптимум h_c: 1.8–2.5 м"))

    def set_target_carbon(self, c_target: float) -> None:
        self._target_c = c_target

    def set_theme(self, theme: str) -> None:
        self._theme = theme

    def _colors(self) -> dict[str, str]:
        return app_theme.tokens(self._theme or get_theme())

    def set_state(self, snapshot: dict[str, Any] | None) -> None:
        if not snapshot:
            self._eff_value.setText("η·Z —" if self._compact else "—")
            self._phi_text.setText("Φ —" if self._compact else "Φ = —")
            if self._foam_text is not None:
                self._foam_text.setText("Δh = — м")
            self._dc_value.setText("Δ[C] —" if self._compact else "Δ[C] = —")
            return

        t = self._colors()
        eta = float(snapshot.get("eta_CO", 0.0))
        z_val = float(snapshot.get("Z", 0.0))
        eff = eta * z_val
        self._eff_value.setText(f"η·Z {eff:.2f}")

        phi = float(snapshot.get("Phi", 0.0))
        dh = float(snapshot.get("dh_foam", 0.0))
        warn = CALIB_DEFAULTS["phi_warn"]
        alarm = CALIB_DEFAULTS["phi_alarm"]
        if phi < warn:
            color = t["control_success_green"]
        elif phi < alarm:
            color = t["control_warn"]
        else:
            color = t["control_danger"]
        r = 7 if self._compact else 14
        self._phi_light.setStyleSheet(
            f"background: {color}; border-radius: {r}px; min-width: {2*r}px; min-height: {2*r}px;"
        )
        if self._compact:
            self._phi_text.setText(f"Φ {phi:.2f}")
        else:
            self._phi_text.setText(f"Φ = {phi:.2f}")
            self._foam_text.setText(f"Δh пены = {dh:.2f} м")

        if self._eff_bar is not None:
            self._eff_bar.setValue(int(min(50, eff * 2.5)))

        c_dyn = float(snapshot.get("C", 0.0))
        delta = self._target_c - c_dyn
        dc_txt = f"Δ[C] {delta:+.3f}%"
        self._dc_value.setText(dc_txt)
        if abs(delta) > 0.02:
            self._dc_value.setStyleSheet(
                f"color: {t['control_danger']}; font-weight: bold;"
            )
            if self._dc_hint is not None:
                self._dc_hint.setText(
                    tr("DynamicsIndicators", "Измените время продувки или режим")
                )
        else:
            self._dc_value.setStyleSheet(f"color: {t['text']};")
            if self._dc_hint is not None:
                self._dc_hint.setText("")
