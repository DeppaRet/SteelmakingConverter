"""Панель ручного управления управляющими воздействиями оператора конвертера."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import app_theme
from melt_dynamics import HC_MAX, HC_MIN, MeltDynamicsEngine
from theme_settings import get_theme

KEY_P_O2_MANUAL = "p_o2_manual_enabled"

# Ключи параметров (внутренние имена виджетов / пресетов)
KEY_TARGET_C = "target_carbon"
KEY_O2_LOSSES = "o2_losses"
KEY_FLOW = "blast_flow_m3_min"
KEY_TIME = "blow_time_min"
KEY_LANCE = "lance_height_m"
KEY_LOCKS = "locks"
KEY_COMPUTED = "computed_key"
KEY_BLOW_VOLUME_DISPLAY = "blow_volume_display_m3"

# Только информационная пара i / τ (V — результат расчёта, read-only)
TRIPLET_KEYS = (KEY_FLOW, KEY_TIME)

# Ключи сигнала controls_changed (согласованы с OperForm._on_controls_changed)
SIGNAL_TARGET_C = "target_carbon"
SIGNAL_LANCE = "lance_height"
SIGNAL_O2_LOSSES = "o2_losses"
SIGNAL_BLOW_INTENSITY = "blow_intensity"
SIGNAL_BLOW_TIME = "blow_time"


class ControlKnob(QtWidgets.QFrame):
    """Композит: название, QSlider, QDoubleSpinBox; QDial только в широком режиме."""

    value_changed = pyqtSignal(str, float)

    def __init__(
        self,
        param_key: str,
        title: str,
        unit: str,
        vmin: float,
        vmax: float,
        step: float,
        decimals: int = 1,
        lockable: bool = True,
        compact: bool = True,
        info_hint: str = "",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.param_key = param_key
        self._unit = unit
        self._vmin = vmin
        self._vmax = vmax
        self._step = step
        self._decimals = decimals
        self._lockable = lockable
        self._block = False
        self._is_computed = False

        self.setObjectName("control_knob_frame")
        self.setProperty("class", "control_knob_frame")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 3, 4, 3)
        lay.setSpacing(2)

        title_row = QtWidgets.QHBoxLayout()
        self._title_lbl = QtWidgets.QLabel(title)
        self._title_lbl.setProperty("class", "control_knob_title")
        self._title_lbl.setWordWrap(True)
        self._value_lbl = QtWidgets.QLabel(f"— {unit}")
        self._value_lbl.setProperty("class", "control_knob_value")
        self._value_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self._value_lbl.setMinimumWidth(72)
        title_row.addWidget(self._title_lbl, 1)
        title_row.addWidget(self._value_lbl, 0)
        self._title_row_lay = title_row
        lay.addLayout(title_row)

        n_steps = max(1, int((vmax - vmin) / step))

        self._dial = QtWidgets.QDial()
        self._dial.setNotchesVisible(True)
        self._dial.setWrapping(False)
        self._dial.setMinimum(0)
        self._dial.setMaximum(n_steps)
        if compact:
            self._dial.setFixedSize(0, 0)
            self._dial.hide()
        else:
            self._dial.setFixedSize(36, 36)

        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(n_steps)
        self._slider.setMinimumHeight(14)

        self._spin = QtWidgets.QDoubleSpinBox()
        self._spin.setProperty("class", "control_spin")
        self._spin.setRange(vmin, vmax)
        self._spin.setSingleStep(step)
        self._spin.setDecimals(decimals)
        self._spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self._spin.setMinimumWidth(56)
        self._spin.setMaximumWidth(88)

        ctrl_row = QtWidgets.QHBoxLayout()
        ctrl_row.setSpacing(4)
        if not compact:
            ctrl_row.addWidget(self._dial)
        ctrl_row.addWidget(self._slider, 1)
        ctrl_row.addWidget(self._spin)
        lay.addLayout(ctrl_row)

        self._info_hint_lbl = None
        if info_hint:
            hint_lbl = QtWidgets.QLabel(info_hint)
            hint_lbl.setProperty("class", "control_info_hint")
            hint_lbl.setWordWrap(True)
            self._info_hint_lbl = hint_lbl
            lay.addWidget(hint_lbl)

        if lockable:
            self._lock = QtWidgets.QCheckBox("Фикс.")
            self._lock.setProperty("class", "control_lock")
            self._lock.setToolTip(
                "Зафиксировать; второй параметр пересчитается по V/i или V/τ "
                "(V — расчётное дутьё над панелью)"
            )
            lay.addWidget(self._lock)
        else:
            self._lock = None

        self._tab_embed_heights: tuple[int, int] | None = None

        self._dial.valueChanged.connect(self._from_dial)
        self._slider.valueChanged.connect(self._from_slider)
        self._spin.valueChanged.connect(self._from_spin)
        if self._lock is not None:
            self._lock.toggled.connect(lambda _: self.value_changed.emit(self.param_key, self.value()))

    def _to_steps(self, val: float) -> int:
        val = max(self._vmin, min(self._vmax, val))
        return int(round((val - self._vmin) / self._step))

    def _from_steps(self, step: int) -> float:
        return round(self._vmin + step * self._step, self._decimals)

    def _sync_widgets(self, val: float, source: str) -> None:
        self._block = True
        val = max(self._vmin, min(self._vmax, val))
        step = self._to_steps(val)
        if source != "dial":
            self._dial.setValue(step)
        if source != "slider":
            self._slider.setValue(step)
        if source != "spin":
            self._spin.setValue(val)
        self._value_lbl.setText(f"{val:.{self._decimals}f} {self._unit}")
        self._block = False

    def _from_dial(self, step: int) -> None:
        if self._block:
            return
        self._emit(self._from_steps(step), "dial")

    def _from_slider(self, step: int) -> None:
        if self._block:
            return
        self._emit(self._from_steps(step), "slider")

    def _from_spin(self, val: float) -> None:
        if self._block:
            return
        self._emit(val, "spin")

    def _emit(self, val: float, source: str) -> None:
        self._sync_widgets(val, source)
        if not self._is_computed:
            self.value_changed.emit(self.param_key, val)

    def value(self) -> float:
        return float(self._spin.value())

    def set_value(self, val: float, *, emit: bool = False) -> None:
        self._sync_widgets(val, "")
        if emit and not self._is_computed:
            self.value_changed.emit(self.param_key, val)

    def set_range(self, vmin: float, vmax: float) -> None:
        self._vmin = vmin
        self._vmax = vmax
        n_steps = max(1, int((vmax - vmin) / self._step))
        self._dial.setMaximum(n_steps)
        self._slider.setMaximum(n_steps)
        self._spin.setRange(vmin, vmax)

    def set_computed(self, computed: bool) -> None:
        self._is_computed = computed
        self._dial.setEnabled(not computed)
        self._slider.setEnabled(not computed)
        self._spin.setReadOnly(computed)
        cls = "control_spin_computed" if computed else "control_spin"
        self._spin.setProperty("class", cls)
        self._spin.style().unpolish(self._spin)
        self._spin.style().polish(self._spin)
        if self._lock is not None:
            self._lock.setEnabled(not computed)

    def is_locked(self) -> bool:
        return self._lock.isChecked() if self._lock is not None else False

    def set_locked(self, locked: bool) -> None:
        if self._lock is not None:
            self._lock.setChecked(locked)

    def set_hint(self, level: str) -> None:
        """level: '', 'warning', 'danger' — только подсветка значения."""
        if level == "warning":
            self._value_lbl.setStyleSheet("color: #e6a817; font-size: 9px; font-weight: bold;")
        elif level == "danger":
            self._value_lbl.setStyleSheet("color: #e04040; font-size: 9px; font-weight: bold;")
        else:
            self._value_lbl.setStyleSheet("")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_recommended_tooltip(self, text: str) -> None:
        self._spin.setToolTip(text)
        self._title_lbl.setToolTip(text)

    def apply_tab_embed_style(self) -> None:
        """Высота и отступы для вкладки «Симуляция» (без наложения строк)."""
        self._title_lbl.setWordWrap(False)
        lay = self.layout()
        if lay is not None:
            lay.setContentsMargins(6, 6, 6, 6)
            lay.setSpacing(5)
        if self._info_hint_lbl is not None:
            self._info_hint_lbl.hide()
        if lay is not None and self._lock is not None:
            lay.removeWidget(self._lock)
            self._title_row_lay.addWidget(self._lock, 0, QtCore.Qt.AlignVCenter)
        h = 64
        self.setFixedHeight(h)
        self.setMinimumHeight(h)
        self.setMaximumHeight(h)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )


class ControlInputsPanel(QtWidgets.QWidget):
    """Панель «Управляющие воздействия» для формы оператора."""

    controls_changed = pyqtSignal(dict)
    layout_geometry_changed = pyqtSignal()
    apply_recalc_requested = pyqtSignal()
    simulate_requested = pyqtSignal()
    preset_save_requested = pyqtSignal()
    preset_load_requested = pyqtSignal()

    def compute_derived(
        self,
        g_metal_t: float = 200.0,
        si_pig: float = 0.5,
    ) -> dict[str, float]:
        """η_CO, Z, P_O2, K_P, G_V через MeltDynamicsEngine (h_c до 3,3 м)."""
        h_c = self._knob_lance.value()
        i_total = self._knob_flow.value()
        return MeltDynamicsEngine.preview_free_params(
            h_c, i_total, g_metal_t, si_pig
        )

    def lance_height_value(self) -> float:
        return self._knob_lance.value()

    def intensity_value(self) -> float:
        return self._knob_flow.value()

    def target_carbon_value(self) -> float:
        return self._knob_target_c.value()

    def p_o2_manual_mode(self) -> bool:
        return self._p_o2_manual_cb.isChecked()

    def p_o2_manual_value(self) -> float:
        return self._knob_o2.value()

    def p_o2_auto_value(self) -> float:
        return self.compute_derived()["p_o2"]

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("control_inputs_panel")
        self._scenario_name = ""
        self._presets_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "presets"
        )
        self._reference_volume_m3 = 8000.0
        self._debounce = QtCore.QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(200)
        self._debounce.timeout.connect(self._emit_controls)
        self._pending_log: list[tuple[str, float, float]] = []

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        self._group = QtWidgets.QGroupBox("Управляющие воздействия")
        self._group.setObjectName("control_inputs_group")
        grp_lay = QtWidgets.QVBoxLayout(self._group)
        grp_lay.setContentsMargins(4, 8, 4, 4)
        grp_lay.setSpacing(4)

        self._knob_grid = QtWidgets.QGridLayout()
        grid = self._knob_grid
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(8)

        info_hint = "информационный параметр,\nне влияет на химию"

        self._knob_target_c = ControlKnob(
            KEY_TARGET_C, "Целевое [C]_М", "%", 0.02, 0.30, 0.01, decimals=3, lockable=False
        )
        self._knob_lance = ControlKnob(
            KEY_LANCE, "Фурма h_c", "м", HC_MIN, HC_MAX, 0.05, decimals=2, lockable=False
        )
        self._knob_o2 = ControlKnob(
            KEY_O2_LOSSES, "Потери O₂ (ручн.)", "%", 5.0, 10.0, 0.5, decimals=1, lockable=False
        )
        self._knob_flow = ControlKnob(
            KEY_FLOW, "Расход O₂ i", "м³/мин", 50.0, 1200.0, 5.0,
            decimals=0, info_hint=info_hint,
        )
        self._knob_time = ControlKnob(
            KEY_TIME, "Время продувки τ", "мин", 12.0, 25.0, 0.5,
            decimals=1, info_hint=info_hint,
        )

        self._knobs: dict[str, ControlKnob] = {
            KEY_TARGET_C: self._knob_target_c,
            KEY_LANCE: self._knob_lance,
            KEY_O2_LOSSES: self._knob_o2,
            KEY_FLOW: self._knob_flow,
            KEY_TIME: self._knob_time,
        }

        # Строка 1: активные крутилки
        grid.addWidget(self._knob_target_c, 0, 0)
        grid.addWidget(self._knob_lance, 0, 1)

        self._o2_cell = QtWidgets.QFrame()
        self._o2_cell.setObjectName("control_po2_frame")
        self._o2_cell.setProperty("class", "control_knob_frame")
        o2_cell = self._o2_cell
        o2_lay = QtWidgets.QVBoxLayout(o2_cell)
        o2_lay.setContentsMargins(6, 5, 6, 5)
        o2_lay.setSpacing(4)
        po2_title = QtWidgets.QLabel("П_O₂ (авто)")
        po2_title.setProperty("class", "control_knob_title")
        self._p_o2_auto = QtWidgets.QLineEdit()
        self._p_o2_auto.setReadOnly(True)
        self._p_o2_auto.setFixedHeight(22)
        self._p_o2_auto.setProperty("class", "control_blow_volume_readonly")
        self._p_o2_manual_cb = QtWidgets.QCheckBox("Ручной режим П_O₂")
        self._p_o2_manual_cb.setProperty("class", "control_lock")
        o2_lay.addWidget(po2_title)
        o2_lay.addWidget(self._p_o2_auto)
        o2_lay.addWidget(self._p_o2_manual_cb)
        o2_lay.addWidget(self._knob_o2)
        self._knob_o2.hide()
        grid.addWidget(o2_cell, 0, 2)

        # Строка 2: информационные + индикатор η·Z
        grid.addWidget(self._knob_flow, 1, 0)
        grid.addWidget(self._knob_time, 1, 1)

        self._efficiency_frame = QtWidgets.QFrame()
        self._efficiency_frame.setProperty("class", "control_efficiency_frame")
        eff_lay = QtWidgets.QVBoxLayout(self._efficiency_frame)
        eff_lay.setContentsMargins(4, 2, 4, 2)
        eff_lay.setSpacing(2)
        self._eff_title = QtWidgets.QLabel("η_CO · Z")
        self._eff_title.setProperty("class", "control_knob_title")
        self._eff_value = QtWidgets.QLabel("—")
        self._eff_value.setProperty("class", "control_efficiency_value")
        self._eff_value.setAlignment(QtCore.Qt.AlignCenter)
        self._eff_eta_z = QtWidgets.QLabel("")
        self._eff_eta_z.setProperty("class", "control_info_hint")
        self._eff_eta_z.setAlignment(QtCore.Qt.AlignCenter)
        eff_lay.addWidget(self._eff_title)
        eff_lay.addWidget(self._eff_value)
        eff_lay.addWidget(self._eff_eta_z)
        grid.addWidget(self._efficiency_frame, 1, 2)

        self._grp_lay = grp_lay
        grp_lay.addLayout(grid)

        # Read-only расход дутья (результат расчёта)
        vol_row = QtWidgets.QHBoxLayout()
        vol_lbl = QtWidgets.QLabel("Расход дутья (расчётный):")
        vol_lbl.setProperty("class", "control_knob_title")
        self._blow_volume_display = QtWidgets.QLineEdit()
        self._blow_volume_display.setReadOnly(True)
        self._blow_volume_display.setProperty("class", "control_blow_volume_readonly")
        self._blow_volume_display.setPlaceholderText("— м³")
        self._blow_volume_display.setMinimumWidth(80)
        vol_row.addWidget(vol_lbl)
        vol_row.addWidget(self._blow_volume_display, 1)
        grp_lay.addLayout(vol_row)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(4)
        self._btn_reset = QtWidgets.QPushButton("Сброс")
        self._btn_save = QtWidgets.QPushButton("Сохр.")
        self._btn_save.setToolTip("Сохранить пресет")
        self._btn_load = QtWidgets.QPushButton("Загр.")
        self._btn_load.setToolTip("Загрузить пресет")
        for b in (self._btn_reset, self._btn_save, self._btn_load):
            b.setProperty("class", "control_tool_btn")
        btn_row.addWidget(self._btn_reset)
        btn_row.addWidget(self._btn_save)
        btn_row.addWidget(self._btn_load)
        grp_lay.addLayout(btn_row)

        self._btn_main_row = QtWidgets.QHBoxLayout()
        btn_main_row = self._btn_main_row
        btn_main_row.setSpacing(6)
        self._btn_simulate = QtWidgets.QPushButton("Симулировать плавку")
        self._btn_simulate.setObjectName("control_simulate_btn")
        self._btn_simulate.setToolTip(
            "Пошаговая динамика до целевого [C] (Δt = 30 с)"
        )
        self._btn_simulate.setMinimumHeight(32)
        self._btn_apply = QtWidgets.QPushButton("Применить и пересчитать")
        self._btn_apply.setObjectName("control_apply_btn")
        self._btn_apply.setToolTip(
            "Запустить полный расчёт плавки с текущими значениями крутилок"
        )
        self._btn_apply.setMinimumHeight(32)
        for b in (self._btn_simulate, self._btn_apply):
            b.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed,
            )
        btn_main_row.addWidget(self._btn_simulate, 1)
        btn_main_row.addWidget(self._btn_apply, 1)
        grp_lay.addLayout(btn_main_row)

        root.addWidget(self._group)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )

        self._btn_reset.clicked.connect(self.reset_to_defaults)
        self._btn_save.clicked.connect(self._save_preset_dialog)
        self._btn_load.clicked.connect(self._load_preset_dialog)
        self._btn_apply.clicked.connect(self.apply_recalc_requested.emit)
        self._btn_simulate.clicked.connect(self.simulate_requested.emit)
        self._p_o2_manual_cb.toggled.connect(self._on_p_o2_manual_toggled)

        for knob in self._knobs.values():
            knob.value_changed.connect(self._on_knob_changed)

        self._knob_flow.set_locked(False)
        self._knob_time.set_locked(False)
        self._computed_key = KEY_TIME
        self._apply_computed_state()

        self.reset_to_defaults()
        self.set_theme(get_theme())
        self._on_p_o2_manual_toggled(False)

    def configure_for_tab_embed(self) -> None:
        """Вертикальный стек крутилок для левой половины вкладки «Симуляция»."""
        if getattr(self, "_tab_embed_applied", False):
            return
        self._tab_embed_applied = True
        self._group.setTitle("Управляющие воздействия")
        self._grp_lay.setContentsMargins(6, 8, 6, 6)
        self._grp_lay.setSpacing(5)

        knob_widgets = []
        for i in range(self._knob_grid.count()):
            item = self._knob_grid.itemAt(i)
            if item is not None and item.widget() is not None:
                knob_widgets.append(item.widget())
        for w in knob_widgets:
            self._knob_grid.removeWidget(w)

        self._tab_knob_stack = QtWidgets.QVBoxLayout()
        self._tab_knob_stack.setSpacing(12)
        self._tab_knob_stack.setContentsMargins(0, 0, 0, 0)

        for knob in (
            self._knob_target_c,
            self._knob_lance,
            self._knob_flow,
            self._knob_time,
        ):
            knob.apply_tab_embed_style()

        self._o2_cell_heights = (100, 168)
        self._compact_efficiency_for_tab()

        for w in (
            self._knob_target_c,
            self._knob_lance,
            self._o2_cell,
            self._knob_flow,
            self._knob_time,
            self._efficiency_frame,
        ):
            self._tab_knob_stack.addWidget(w)

        self._grp_lay.removeItem(self._knob_grid)
        self._grp_lay.insertLayout(0, self._tab_knob_stack)

        self._blow_volume_display.setFixedHeight(24)
        for btn in (
            self._btn_simulate,
            self._btn_apply,
            self._btn_reset,
            self._btn_save,
            self._btn_load,
        ):
            btn.setFixedHeight(28)

        self._group.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        self.setMinimumWidth(300)
        self._refresh_tab_panel_min_height()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )
        self._apply_o2_cell_tab_height(manual=self._p_o2_manual_cb.isChecked())

    def scroll_content_min_height(self) -> int:
        """Высота блока внутри прокрутки (без кнопок «Симулировать» / «Применить»)."""
        if not getattr(self, "_tab_embed_applied", False):
            return self.minimumHeight()
        manual = self._p_o2_manual_cb.isChecked()
        o2_h = self._o2_cell_heights[1] if manual else self._o2_cell_heights[0]
        return (
            64 * 4
            + o2_h
            + 34
            + 12 * 5
            + 28
            + 28
            + 28
            + 48
        )

    def detach_main_buttons_for_tab(
        self, footer_layout: QtWidgets.QHBoxLayout,
    ) -> None:
        """Вынести главные кнопки из группы — вниз колонки, вне прокрутки."""
        if getattr(self, "_main_buttons_detached", False):
            return
        self._main_buttons_detached = True
        self._grp_lay.removeItem(self._btn_main_row)
        footer_layout.setSpacing(6)
        footer_layout.setContentsMargins(6, 4, 6, 6)
        for btn in (self._btn_simulate, self._btn_apply):
            btn.setFixedHeight(32)
            btn.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed,
            )
        footer_layout.addWidget(self._btn_simulate, 1)
        footer_layout.addWidget(self._btn_apply, 1)
        self._refresh_tab_panel_min_height()

    def _compact_efficiency_for_tab(self) -> None:
        """Одна строка η·Z вместо трёх налезающих подписей."""
        eff_lay = self._efficiency_frame.layout()
        if eff_lay is None:
            return
        while eff_lay.count():
            item = eff_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._eff_line = QtWidgets.QLabel("η·Z —")
        self._eff_line.setProperty("class", "control_efficiency_value")
        self._eff_line.setAlignment(QtCore.Qt.AlignCenter)
        eff_lay.setContentsMargins(6, 4, 6, 4)
        eff_lay.addWidget(self._eff_line)
        self._efficiency_frame.setFixedHeight(34)
        self._efficiency_frame.setMinimumHeight(34)
        self._efficiency_frame.setMaximumHeight(34)
        self._efficiency_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )

    def _refresh_tab_panel_min_height(self) -> None:
        if not getattr(self, "_tab_embed_applied", False):
            return
        manual = self._p_o2_manual_cb.isChecked()
        o2_h = self._o2_cell_heights[1] if manual else self._o2_cell_heights[0]
        scroll_h = (
            64 * 4
            + o2_h
            + 34
            + 12 * 5
            + 28
            + 28
            + 28
            + 48
        )
        footer = 0 if getattr(self, "_main_buttons_detached", False) else 36
        total = scroll_h + footer
        self.setMinimumHeight(total)
        self._group.setMinimumHeight(scroll_h)
        self._group.setMaximumHeight(scroll_h)
        if getattr(self, "_last_tab_scroll_h", None) != scroll_h:
            self._last_tab_scroll_h = scroll_h
            self.layout_geometry_changed.emit()

    def _apply_o2_cell_tab_height(self, *, manual: bool) -> None:
        if not getattr(self, "_tab_embed_applied", False):
            return
        h = self._o2_cell_heights[1] if manual else self._o2_cell_heights[0]
        self._o2_cell.setFixedHeight(h)
        self._o2_cell.setMinimumHeight(h)
        self._o2_cell.setMaximumHeight(h)
        self._o2_cell.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        self._refresh_tab_panel_min_height()

    def _on_p_o2_manual_toggled(self, checked: bool) -> None:
        if checked:
            self._knob_o2.apply_tab_embed_style()
            self._knob_o2.show()
            self._p_o2_auto.setProperty("class", "control_auto_strikethrough")
        else:
            self._knob_o2.hide()
            self._p_o2_auto.setProperty("class", "control_blow_volume_readonly")
        self._apply_o2_cell_tab_height(manual=checked)
        self._p_o2_auto.style().unpolish(self._p_o2_auto)
        self._p_o2_auto.style().polish(self._p_o2_auto)
        self._update_p_o2_auto_display()
        self._debounce.start()

    def _update_p_o2_auto_display(self) -> None:
        d = self.compute_derived()
        self._p_o2_auto.setText(f"{d['p_o2']:.1f} %")

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self.setStyleSheet(app_theme.control_inputs_panel_qss(theme))
        self._btn_apply.setStyleSheet(app_theme.primary_button_style(theme))
        self._btn_simulate.setStyleSheet(app_theme.secondary_button_style(theme))
        self._update_efficiency_display()

    def set_scenario_name(self, name: str) -> None:
        self._scenario_name = name or ""

    def set_presets_dir(self, path: str) -> None:
        self._presets_dir = path

    def set_target_carbon_range(self, center: float, margin: float = 0.08) -> None:
        """Диапазон крутилки [C] вокруг марочного лимита сценария."""
        vmin = max(0.02, center - margin)
        vmax = min(0.30, center + margin)
        if vmax <= vmin:
            vmax = vmin + 0.05
        self._knob_target_c.set_range(vmin, vmax)

    def set_target_carbon_value(self, value: float) -> None:
        self._knob_target_c.set_value(value)

    def set_blow_volume_display(self, v_m3: float) -> None:
        """Обновить read-only поле расчётного объёма дутья V [м³]."""
        self._reference_volume_m3 = max(v_m3, 1.0)
        self._blow_volume_display.setText(f"{v_m3:.0f} м³")

    def set_informational_blow_rates(self, i_m3_min: float, tau_min: float) -> None:
        """Показать i и τ после расчёта дутья (Ф-2: τ = V/i, i = V/τ), без рассинхрона виджетов."""
        self._knob_flow.set_value(float(i_m3_min))
        self._knob_time.set_value(float(tau_min))

    def _on_knob_changed(self, key: str, new_val: float) -> None:
        old = getattr(self, f"_prev_{key}", new_val)
        setattr(self, f"_prev_{key}", new_val)
        if abs(old - new_val) > 1e-9:
            self._pending_log.append((key, old, new_val))

        if key in TRIPLET_KEYS:
            self._enforce_lock_rules(key)
            self._apply_computed_state()
            self._sync_flow_time_triplet()

        if key in (KEY_LANCE, KEY_FLOW):
            self._update_efficiency_display()
            self._update_p_o2_auto_display()

        self._debounce.start()

    def _enforce_lock_rules(self, changed_key: str) -> None:
        """Не более одной галочки «Фикс.»; без автоматической фиксации второго параметра."""
        if self._knob_flow.is_locked() and self._knob_time.is_locked():
            if changed_key == KEY_FLOW:
                self._knob_time.set_locked(False)
            else:
                self._knob_flow.set_locked(False)
        lock_flow = self._knob_flow.is_locked()
        lock_time = self._knob_time.is_locked()
        if lock_flow and not lock_time:
            self._computed_key = KEY_FLOW
        elif lock_time and not lock_flow:
            self._computed_key = KEY_TIME
        else:
            self._computed_key = ""

    def _apply_computed_state(self) -> None:
        active = bool(self._computed_key)
        for k in TRIPLET_KEYS:
            self._knobs[k].set_computed(active and k == self._computed_key)

    def _sync_flow_time_triplet(self) -> None:
        """Связь i и τ через расчётный V (Ф-2), только если один параметр зафиксирован."""
        if not (self._knob_flow.is_locked() or self._knob_time.is_locked()):
            return
        v = self._reference_volume_m3
        if v <= 0:
            return
        if self._knob_time.is_locked() and not self._knob_flow.is_locked():
            self._knob_flow.set_value(v / max(self._knob_time.value(), 0.1))
        elif self._knob_flow.is_locked() and not self._knob_time.is_locked():
            self._knob_time.set_value(v / max(self._knob_flow.value(), 1.0))

    def set_computed_value(self, key: str, value: float) -> None:
        if key not in self._knobs:
            return
        knob = self._knobs[key]
        was = knob._block
        knob._block = True
        knob._sync_widgets(value, "")
        knob._block = was

    def get_values(self) -> dict[str, Any]:
        locks = {
            KEY_FLOW: self._knob_flow.is_locked(),
            KEY_TIME: self._knob_time.is_locked(),
        }
        o2_val = (
            self._knob_o2.value()
            if self._p_o2_manual_cb.isChecked()
            else self.compute_derived()["p_o2"]
        )
        return {
            KEY_TARGET_C: self._knob_target_c.value(),
            KEY_O2_LOSSES: o2_val,
            KEY_P_O2_MANUAL: self._p_o2_manual_cb.isChecked(),
            KEY_FLOW: self._knob_flow.value(),
            KEY_TIME: self._knob_time.value(),
            KEY_LANCE: self._knob_lance.value(),
            KEY_LOCKS: locks,
            KEY_COMPUTED: self._computed_key,
            KEY_BLOW_VOLUME_DISPLAY: self._reference_volume_m3,
        }

    def get_signal_values(self) -> dict[str, float]:
        """Словарь для сигнала controls_changed (без blow_volume)."""
        vals = self.get_values()
        return {
            SIGNAL_TARGET_C: vals[KEY_TARGET_C],
            SIGNAL_LANCE: vals[KEY_LANCE],
            SIGNAL_O2_LOSSES: vals[KEY_O2_LOSSES],
            SIGNAL_BLOW_INTENSITY: vals[KEY_FLOW],
            SIGNAL_BLOW_TIME: vals[KEY_TIME],
        }

    def set_values(self, data: dict[str, Any], *, emit: bool = False) -> None:
        locks = data.get(KEY_LOCKS, {})
        if KEY_FLOW in locks:
            self._knob_flow.set_locked(bool(locks[KEY_FLOW]))
        if KEY_TIME in locks:
            self._knob_time.set_locked(bool(locks[KEY_TIME]))
        if KEY_COMPUTED in data:
            self._computed_key = data[KEY_COMPUTED]
        if KEY_P_O2_MANUAL in data:
            self._p_o2_manual_cb.setChecked(bool(data[KEY_P_O2_MANUAL]))
        elif "p_o2_manual" in data:
            self._p_o2_manual_cb.setChecked(bool(data["p_o2_manual"]))
        for key in (KEY_TARGET_C, KEY_O2_LOSSES, KEY_FLOW, KEY_TIME, KEY_LANCE):
            if key in data:
                self._knobs[key].set_value(float(data[key]), emit=False)
        if KEY_BLOW_VOLUME_DISPLAY in data:
            self._reference_volume_m3 = float(data[KEY_BLOW_VOLUME_DISPLAY])
            self._blow_volume_display.setText(f"{self._reference_volume_m3:.0f} м³")
        # Обратная совместимость v1: blast_volume_m3 → reference volume
        if "blast_volume_m3" in data:
            self._reference_volume_m3 = float(data["blast_volume_m3"])
            self._blow_volume_display.setText(f"{self._reference_volume_m3:.0f} м³")
        self._apply_computed_state()
        self._on_p_o2_manual_toggled(self._p_o2_manual_cb.isChecked())
        self._update_efficiency_display()
        if emit:
            self._emit_controls()

    def set_recommended(self, recommended: dict[str, float]) -> None:
        labels = {
            KEY_TARGET_C: "Рекомендуемое [C]",
            KEY_FLOW: "Рекомендуемый расход",
            KEY_TIME: "Рекомендуемое время",
            KEY_LANCE: "Рекомендуемая высота фурмы",
            KEY_O2_LOSSES: "Типовые потери O₂",
        }
        for key, val in recommended.items():
            if key in self._knobs:
                tip = f"{labels.get(key, 'Реком.')}: {val}"
                self._knobs[key].set_recommended_tooltip(tip)

    def apply_range_hints(self, hints: dict[str, str]) -> None:
        for key, knob in self._knobs.items():
            knob.set_hint(hints.get(key, ""))

    def reset_to_defaults(self) -> None:
        self._knob_target_c.set_value(0.10)
        self._knob_o2.set_value(7.5)
        self._p_o2_manual_cb.setChecked(False)
        self._knob_flow.set_value(600.0)
        self._knob_time.set_value(17.0)
        self._knob_lance.set_value(1.15)
        self._reference_volume_m3 = 8000.0
        self._blow_volume_display.clear()
        self.apply_range_hints({})
        self._knob_flow.set_locked(False)
        self._knob_time.set_locked(False)
        self._computed_key = KEY_TIME
        self._apply_computed_state()
        self._update_efficiency_display()
        self._debounce.start()

    def _update_efficiency_display(self, g_metal_t: float = 200.0, si_pig: float = 0.5) -> None:
        derived = self.compute_derived(g_metal_t, si_pig)
        eff = derived["efficiency"]
        eta = derived["eta_co"]
        z = derived["z_co"]
        success = eff > 1.8
        green = app_theme.control_success_green(getattr(self, "_theme", None))
        text = f"η·Z {eff:.2f}  (η={eta:.1f}%  Z={z:.3f})"
        if getattr(self, "_tab_embed_applied", False) and hasattr(self, "_eff_line"):
            self._eff_line.setText(text)
            self._eff_line.setStyleSheet(
                f"color: {green}; font-weight: bold;" if success else ""
            )
        else:
            self._eff_value.setText(f"{eff:.2f}")
            self._eff_eta_z.setText(f"η={eta:.1f}%  Z={z:.3f}")
            color = green if success else ""
            weight = "bold" if success else "normal"
            self._eff_value.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: {weight};"
                if success
                else "font-size: 11px;"
            )
        self._efficiency_frame.setProperty("success", success)
        self._efficiency_frame.style().unpolish(self._efficiency_frame)
        self._efficiency_frame.style().polish(self._efficiency_frame)

    def drain_change_log(self) -> list[tuple[str, float, float]]:
        log = self._pending_log[:]
        self._pending_log.clear()
        return log

    def refresh_derived_display(self, g_metal_t: float, si_pig: float = 0.5) -> None:
        """Обновить η·Z и П_O2 (авто) с учётом массы шихты."""
        self._update_efficiency_display(g_metal_t, si_pig)
        self._update_p_o2_auto_display()

    def _emit_controls(self) -> None:
        self.refresh_derived_display(200.0)
        self.controls_changed.emit(self.get_signal_values())

    def build_preset_payload(self) -> dict[str, Any]:
        vals = self.get_values()
        return {
            "schema_version": 3,
            "scenario_name": self._scenario_name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "controls": {
                KEY_TARGET_C: vals[KEY_TARGET_C],
                KEY_O2_LOSSES: vals[KEY_O2_LOSSES],
                KEY_FLOW: vals[KEY_FLOW],
                KEY_TIME: vals[KEY_TIME],
                KEY_LANCE: vals[KEY_LANCE],
                KEY_LOCKS: vals[KEY_LOCKS],
                KEY_COMPUTED: vals[KEY_COMPUTED],
                KEY_P_O2_MANUAL: vals.get(KEY_P_O2_MANUAL, False),
            },
        }

    def _save_preset_dialog(self) -> None:
        os.makedirs(self._presets_dir, exist_ok=True)
        default_name = f"operator_preset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить пресет",
            os.path.join(self._presets_dir, default_name),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.build_preset_payload(), f, ensure_ascii=False, indent=2)
        except OSError as exc:
            QMessageBox.warning(self, "Пресет", f"Не удалось сохранить: {exc}")

    def _load_preset_dialog(self) -> None:
        os.makedirs(self._presets_dir, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить пресет",
            self._presets_dir,
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            controls = data.get("controls", data)
            self.set_values(controls, emit=True)
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
            QMessageBox.warning(self, "Пресет", f"Не удалось загрузить: {exc}")
