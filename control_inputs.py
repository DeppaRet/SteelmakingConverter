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
from theme_settings import get_theme

# Ключи параметров (согласованы с OperForm._on_controls_changed)
KEY_VOLUME = "blast_volume_m3"
KEY_FLOW = "blast_flow_m3_min"
KEY_TIME = "blow_time_min"
KEY_LANCE = "lance_height_m"
KEY_LOCKS = "locks"
KEY_COMPUTED = "computed_key"

TRIPLET_KEYS = (KEY_VOLUME, KEY_FLOW, KEY_TIME)


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

        if lockable:
            self._lock = QtWidgets.QCheckBox("Фикс.")
            self._lock.setProperty("class", "control_lock")
            self._lock.setToolTip("Зафиксировать параметр; третий из V/i/τ вычисляется")
            lay.addWidget(self._lock)
        else:
            self._lock = None

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
        """level: '', 'warning', 'danger' — только подсветка значения, без жёлтой рамки."""
        self.setProperty("warning", False)
        self.setProperty("danger", False)
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


class ControlInputsPanel(QtWidgets.QWidget):
    """Панель «Управляющие воздействия» для формы оператора."""

    controls_changed = pyqtSignal(dict)
    apply_recalc_requested = pyqtSignal()
    preset_save_requested = pyqtSignal()
    preset_load_requested = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("control_inputs_panel")
        self._scenario_name = ""
        self._presets_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "presets"
        )
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
        # Размещение в центральной колонке над этапами расчёта (см. OperForm.setupUi).
        grp_lay = QtWidgets.QVBoxLayout(self._group)
        grp_lay.setContentsMargins(4, 8, 4, 4)
        grp_lay.setSpacing(4)

        self._knobs_layout = QtWidgets.QVBoxLayout()
        self._knobs_layout.setContentsMargins(0, 4, 0, 0)
        self._knobs_layout.setSpacing(6)

        self._knob_volume = ControlKnob(
            KEY_VOLUME, "Объём дутья V", "м³", 500.0, 50000.0, 50.0, decimals=0
        )
        self._knob_flow = ControlKnob(
            KEY_FLOW, "Расход O₂ i", "м³/мин", 200.0, 1200.0, 5.0, decimals=0
        )
        self._knob_time = ControlKnob(
            KEY_TIME, "Время продувки τ", "мин", 12.0, 25.0, 0.5, decimals=1
        )
        self._knob_lance = ControlKnob(
            KEY_LANCE, "Фурма h_c", "м", 0.8, 2.5, 0.05, decimals=2, lockable=False
        )

        self._knobs: dict[str, ControlKnob] = {
            KEY_VOLUME: self._knob_volume,
            KEY_FLOW: self._knob_flow,
            KEY_TIME: self._knob_time,
            KEY_LANCE: self._knob_lance,
        }

        for knob in (
            self._knob_volume,
            self._knob_flow,
            self._knob_time,
            self._knob_lance,
        ):
            self._knobs_layout.addWidget(knob)
            knob.setMinimumHeight(52)

        grp_lay.addLayout(self._knobs_layout)

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

        self._btn_apply = QtWidgets.QPushButton("Применить и пересчитать")
        self._btn_apply.setObjectName("control_apply_btn")
        self._btn_apply.setToolTip(
            "Запустить полный расчёт плавки с текущими значениями крутилок"
        )
        self._btn_apply.setMinimumHeight(32)
        self._btn_apply.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed,
        )
        grp_lay.addWidget(self._btn_apply)

        root.addWidget(self._group)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )

        self._btn_reset.clicked.connect(self.reset_to_defaults)
        self._btn_save.clicked.connect(self._save_preset_dialog)
        self._btn_load.clicked.connect(self._load_preset_dialog)
        self._btn_apply.clicked.connect(self.apply_recalc_requested.emit)

        for knob in self._knobs.values():
            knob.value_changed.connect(self._on_knob_changed)

        self._knob_volume.set_locked(True)
        self._knob_flow.set_locked(True)
        self._computed_key = KEY_TIME
        self._apply_computed_state()

        self.reset_to_defaults()
        self.set_theme(get_theme())

    def set_theme(self, theme: str) -> None:
        self.setStyleSheet(app_theme.control_inputs_panel_qss(theme))
        self._btn_apply.setStyleSheet(app_theme.primary_button_style(theme))

    def set_scenario_name(self, name: str) -> None:
        self._scenario_name = name or ""

    def set_presets_dir(self, path: str) -> None:
        self._presets_dir = path

    def _on_knob_changed(self, key: str, new_val: float) -> None:
        old = getattr(self, f"_prev_{key}", new_val)
        setattr(self, f"_prev_{key}", new_val)
        if abs(old - new_val) > 1e-9:
            self._pending_log.append((key, old, new_val))

        if key in TRIPLET_KEYS:
            self._enforce_lock_rules(key)
            self._apply_computed_state()

        self._debounce.start()

    def _enforce_lock_rules(self, changed_key: str) -> None:
        """Два фиксированных параметра из тройки V/i/τ; третий — вычисляемый."""
        locks = {
            KEY_VOLUME: self._knob_volume.is_locked(),
            KEY_FLOW: self._knob_flow.is_locked(),
            KEY_TIME: self._knob_time.is_locked(),
        }
        locked_count = sum(locks.values())
        if locked_count < 2:
            if changed_key == KEY_VOLUME:
                self._knob_flow.set_locked(True)
            elif changed_key == KEY_FLOW:
                self._knob_time.set_locked(True)
            else:
                self._knob_volume.set_locked(True)
        elif locked_count > 2:
            for k, knob in self._knobs.items():
                if k in TRIPLET_KEYS and k != changed_key:
                    knob.set_locked(False)
                    break
            self._knob_volume.set_locked(True)
            self._knob_flow.set_locked(True)

        locks = {
            KEY_VOLUME: self._knob_volume.is_locked(),
            KEY_FLOW: self._knob_flow.is_locked(),
            KEY_TIME: self._knob_time.is_locked(),
        }
        for k in TRIPLET_KEYS:
            if not locks[k]:
                self._computed_key = k
                break

    def _apply_computed_state(self) -> None:
        for k in TRIPLET_KEYS:
            self._knobs[k].set_computed(k == self._computed_key)

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
            KEY_VOLUME: self._knob_volume.is_locked(),
            KEY_FLOW: self._knob_flow.is_locked(),
            KEY_TIME: self._knob_time.is_locked(),
        }
        return {
            KEY_VOLUME: self._knob_volume.value(),
            KEY_FLOW: self._knob_flow.value(),
            KEY_TIME: self._knob_time.value(),
            KEY_LANCE: self._knob_lance.value(),
            KEY_LOCKS: locks,
            KEY_COMPUTED: self._computed_key,
        }

    def set_values(self, data: dict[str, Any], *, emit: bool = False) -> None:
        locks = data.get(KEY_LOCKS, {})
        if KEY_VOLUME in locks:
            self._knob_volume.set_locked(bool(locks[KEY_VOLUME]))
        if KEY_FLOW in locks:
            self._knob_flow.set_locked(bool(locks[KEY_FLOW]))
        if KEY_TIME in locks:
            self._knob_time.set_locked(bool(locks[KEY_TIME]))
        if KEY_COMPUTED in data:
            self._computed_key = data[KEY_COMPUTED]
        for key in (KEY_VOLUME, KEY_FLOW, KEY_TIME, KEY_LANCE):
            if key in data:
                self._knobs[key].set_value(float(data[key]), emit=False)
        self._apply_computed_state()
        if emit:
            self._emit_controls()

    def set_recommended(self, recommended: dict[str, float]) -> None:
        labels = {
            KEY_VOLUME: "Рекомендуемый объём",
            KEY_FLOW: "Рекомендуемый расход",
            KEY_TIME: "Рекомендуемое время",
            KEY_LANCE: "Рекомендуемая высота фурмы",
        }
        for key, val in recommended.items():
            if key in self._knobs:
                tip = f"{labels.get(key, 'Реком.')}: {val}"
                self._knobs[key].set_recommended_tooltip(tip)

    def apply_range_hints(self, hints: dict[str, str]) -> None:
        for key, knob in self._knobs.items():
            knob.set_hint(hints.get(key, ""))

    def reset_to_defaults(self) -> None:
        self._knob_volume.set_value(8000.0)
        self._knob_flow.set_value(600.0)
        self._knob_time.set_value(17.0)
        self._knob_lance.set_value(1.15)
        self.apply_range_hints({})
        self._knob_volume.set_locked(True)
        self._knob_flow.set_locked(True)
        self._computed_key = KEY_TIME
        self._apply_computed_state()
        self._debounce.start()

    def drain_change_log(self) -> list[tuple[str, float, float]]:
        log = self._pending_log[:]
        self._pending_log.clear()
        return log

    def _emit_controls(self) -> None:
        self.controls_changed.emit(self.get_values())

    def build_preset_payload(self) -> dict[str, Any]:
        vals = self.get_values()
        return {
            "schema_version": 1,
            "scenario_name": self._scenario_name,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "controls": {
                KEY_VOLUME: vals[KEY_VOLUME],
                KEY_FLOW: vals[KEY_FLOW],
                KEY_TIME: vals[KEY_TIME],
                KEY_LANCE: vals[KEY_LANCE],
                KEY_LOCKS: vals[KEY_LOCKS],
                KEY_COMPUTED: vals[KEY_COMPUTED],
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
