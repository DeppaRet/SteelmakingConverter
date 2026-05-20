"""
Динамическая модель плавки в кислородном конвертере (шаг Δt = 30 с).

Источники:
- А.Н. Шаповалов. Технология и расчёт плавки стали в кислородных конвертерах. МИСиС, 2011.
- Шакиров М.К. и др. Прогнозирование содержания углерода… // Изв. вузов. Чёрная металлургия, 2023.
- Конвертерное производство стали (учебная лекция) — диапазоны h_c, v_C, пыли.
- Foaming Index of CaO-SiO2-FeO-MgO, Pyrometallurgy 2016.
- SAIMM Lahiri «Foaminess of slag», 2004.
"""

from __future__ import annotations

import math
import random
from copy import deepcopy
from typing import Any

HC_MIN = 0.8
HC_MAX = 3.3

CALIB_DEFAULTS: dict[str, float] = {
    "k1": 0.058,
    "k2": 0.05,
    "C_kr": 0.40,
    "C0": 0.03,
    "eta_CO_min": 5.0,
    "eta_CO_max": 15.0,
    "h_c_min": HC_MIN,
    "h_c_max": HC_MAX,
    "alpha_i_eta": 0.05,
    "i_ud_ref": 4.0,
    "Z_min": 0.10,
    "Z_max": 0.30,
    "K_P_base": 200.0,
    "alpha_h_KP": 0.25,
    "alpha_i_KP": 0.05,
    "G_V_base": 1.0,
    "beta_h_GV": 0.8,
    "beta_Si_GV": 2.0,
    "Si_threshold": 0.9,
    "P_O2_min": 5.0,
    "P_O2_max": 10.0,
    "foaming_index_base": 0.6,
    "H_free_board": 7.0,
    "phi_warn": 0.5,
    "phi_alarm": 0.9,
    "dt_sec": 30.0,
    "noise_pct": 0.0,
    "cp_steel": 0.84,
    "Q_CO_to_CO2": 282980.0,
    "M_CO": 28.0,
    "heat_loss_per_step_C": 0.8,
    "dT_C_scale": 1.05,
    "dT_C_kJ_per_pct_kg": 1400.0,
    "T_boost_stage1": 6.8,
    "foaming_v_scale": 3.5,
    "neck_area_m2": 25.0,
}


def _xi_h(h_c: float, calib: dict[str, float]) -> float:
    span = calib["h_c_max"] - calib["h_c_min"]
    if span <= 0:
        return 0.0
    return max(0.0, min(1.0, (h_c - calib["h_c_min"]) / span))


class MeltDynamicsEngine:
    """Пошаговая динамика плавки; статические формулы Ф-Д2…Ф-Д6 для баланса Шаповалова."""

    def __init__(
        self,
        initial_state: dict[str, Any] | None = None,
        control_params: dict[str, Any] | None = None,
        calib: dict[str, float] | None = None,
    ) -> None:
        self.calib = {**CALIB_DEFAULTS, **(calib or {})}
        cp = control_params or {}
        init = initial_state or {}
        g_metal_t = float(init.get("G_metal_t", 200.0))
        self.state: dict[str, Any] = {
            "t": float(init.get("t", 0.0)),
            "C": float(init.get("C", 4.0)),
            "Si": float(init.get("Si", 0.5)),
            "Mn": float(init.get("Mn", 0.3)),
            "T": float(init.get("T", 1350.0)),
            "G_metal_t": g_metal_t,
            "G_metal_kg": g_metal_t * 1000.0,
            "h_c": float(cp.get("h_c", 1.5)),
            "i_total": float(cp.get("i_total", 600.0)),
            "FeO_slag": float(init.get("FeO_slag", 15.0)),
            "V_O2_total": float(init.get("V_O2_total", 0.0)),
            "Si_pig": float(init.get("Si_pig", init.get("Si", 0.5))),
            "target_c": float(cp.get("target_c", 0.12)),
        }

    @staticmethod
    def specific_intensity(i_total: float, mass_steel_t: float) -> float:
        """i_уд = i / G_ст [м³/(т·мин)]. Формула (53) методики Шаповалова."""
        if mass_steel_t <= 0:
            return 0.0
        return i_total / mass_steel_t

    def _v_C(self, c_curr: float, i_ud: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д1 ===
        if c_curr >= self.calib["C_kr"]:
            return self.calib["k1"] * i_ud
        return self.calib["k2"] * 60.0 * max(c_curr - self.calib["C0"], 0.0)

    def eta_CO(self, h_c: float, i_ud: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д2 (расширение Ф-A) ===
        xi = _xi_h(h_c, self.calib)
        f_i = 1.0 - self.calib["alpha_i_eta"] * (i_ud - self.calib["i_ud_ref"])
        f_i = max(0.5, min(1.2, f_i))
        eta = self.calib["eta_CO_min"] + (
            self.calib["eta_CO_max"] - self.calib["eta_CO_min"]
        ) * xi * f_i
        return max(self.calib["eta_CO_min"], min(self.calib["eta_CO_max"], eta))

    def Z(self, h_c: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д3 (Ф-B) ===
        xi = _xi_h(h_c, self.calib)
        return self.calib["Z_max"] - (self.calib["Z_max"] - self.calib["Z_min"]) * xi

    def K_P(self, h_c: float, i_ud: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д4 ===
        xi = _xi_h(h_c, self.calib)
        k = self.calib["K_P_base"] * (
            1.0
            + self.calib["alpha_h_KP"] * (1.0 - xi)
            + self.calib["alpha_i_KP"] * (i_ud - self.calib["i_ud_ref"])
        )
        return max(150.0, min(250.0, k))

    def G_V(self, h_c: float, si_pig_iron: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д5 ===
        xi = _xi_h(h_c, self.calib)
        g = self.calib["G_V_base"] + self.calib["beta_h_GV"] * (1.0 - xi) ** 2
        if si_pig_iron > self.calib["Si_threshold"]:
            g += self.calib["beta_Si_GV"] * (si_pig_iron - self.calib["Si_threshold"])
        return max(1.0, min(3.0, g))

    def P_O2(self, h_c: float) -> float:
        # === DYNAMIC EXTENSION v3: формула Ф-Д6 ===
        xi = _xi_h(h_c, self.calib)
        return (
            self.calib["P_O2_min"]
            + (self.calib["P_O2_max"] - self.calib["P_O2_min"]) * xi
        )

    def _foaming(
        self, feo_pct: float, v_o2_rate_m3_min: float
    ) -> tuple[float, float, float]:
        # === DYNAMIC EXTENSION v3: формула Ф-Д7 ===
        feo_norm = min(feo_pct, 25.0) / 25.0
        sigma = self.calib["foaming_index_base"] * (
            1.0 + 1.5 * feo_norm * (1.0 - feo_norm * 0.5)
        )
        area = max(self.calib["neck_area_m2"], 1.0)
        v_gs = v_o2_rate_m3_min / 60.0 / area
        delta_h = sigma * v_gs * self.calib.get("foaming_v_scale", 3.5)
        phi = delta_h / self.calib["H_free_board"]
        return sigma, delta_h, phi

    def step(self) -> dict[str, Any]:
        # === DYNAMIC EXTENSION v3: формула Ф-Д8 — шаг плавки ===
        s = self.state
        dt_min = self.calib["dt_sec"] / 60.0
        i_ud = self.specific_intensity(s["i_total"], s["G_metal_t"])

        eta_co = self.eta_CO(s["h_c"], i_ud)
        z_val = self.Z(s["h_c"])
        k_p = self.K_P(s["h_c"], i_ud)
        p_o2 = self.P_O2(s["h_c"])
        g_v = self.G_V(s["h_c"], s["Si_pig"])

        v_c = self._v_C(s["C"], i_ud)
        if self.calib["noise_pct"] > 0:
            v_c *= 1.0 + random.uniform(-1, 1) * self.calib["noise_pct"] / 100.0

        d_c = -v_c * dt_min
        s["C"] = max(self.calib["C0"], s["C"] + d_c)

        s["Si"] *= math.exp(-dt_min / 2.0)
        s["Mn"] *= math.exp(-dt_min / 2.5)

        if abs(d_c) > 1e-12 and s["G_metal_kg"] > 0:
            o2_for_c = abs(d_c) * s["G_metal_kg"] / 100.0 * 0.5 * 22.4 / 12.0
            s["V_O2_total"] += o2_for_c / max(1.0 - p_o2 / 100.0, 0.5)

        g_co_kg = abs(d_c) / 100.0 * s["G_metal_kg"] * 28.0 / 12.0
        n_co_mol = g_co_kg * 1000.0 / self.calib["M_CO"]
        q_post_kj = (
            eta_co
            / 100.0
            * z_val
            * n_co_mol
            * self.calib["Q_CO_to_CO2"]
            / 1000.0
        )
        thermal_mass = self.calib["cp_steel"] * max(s["G_metal_kg"], 1.0)
        d_t_post = q_post_kj / thermal_mass if thermal_mass > 0 else 0.0
        d_t_c = (
            self.calib["dT_C_scale"]
            * abs(d_c)
            / 100.0
            * s["G_metal_kg"]
            * self.calib["dT_C_kJ_per_pct_kg"]
            / thermal_mass
            if thermal_mass > 0
            else 0.0
        )
        t_boost = (
            self.calib.get("T_boost_stage1", 0.0)
            if s["C"] >= self.calib["C_kr"]
            else 0.0
        )
        s["T"] += d_t_post + d_t_c + t_boost - self.calib["heat_loss_per_step_C"]

        if s["C"] < self.calib["C_kr"]:
            s["FeO_slag"] = min(25.0, s["FeO_slag"] + 0.55 * dt_min)
        elif s["C"] < 0.9:
            s["FeO_slag"] = min(20.0, s["FeO_slag"] + 0.15 * dt_min)

        sigma, dh_foam, phi = self._foaming(s["FeO_slag"], s["i_total"])
        s["t"] += self.calib["dt_sec"]

        return {
            "t_min": s["t"] / 60.0,
            "h_c": s["h_c"],
            "C": s["C"],
            "Si": s["Si"],
            "Mn": s["Mn"],
            "T": s["T"],
            "v_C": v_c,
            "eta_CO": eta_co,
            "Z": z_val,
            "FeO_slag": s["FeO_slag"],
            "K_P": k_p,
            "P_O2": p_o2,
            "G_V": g_v,
            "Sigma": sigma,
            "dh_foam": dh_foam,
            "Phi": phi,
            "i_ud": i_ud,
            "efficiency": eta_co * z_val,
        }

    def run_until_target(
        self, c_target: float, max_steps: int = 200
    ) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []
        for _ in range(max_steps):
            snap = self.step()
            snapshots.append(deepcopy(snap))
            if snap["C"] <= c_target + 1e-6:
                break
        return snapshots

    @classmethod
    def preview_free_params(
        cls,
        h_c: float,
        i_total: float,
        g_metal_t: float,
        si_pig: float = 0.5,
        calib: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Статический расчёт η_CO, Z, P_O2, K_P, G_V без пошаговой симуляции."""
        eng = cls(
            initial_state={"G_metal_t": g_metal_t, "Si_pig": si_pig},
            control_params={"h_c": h_c, "i_total": i_total},
            calib=calib,
        )
        i_ud = cls.specific_intensity(i_total, g_metal_t)
        eta = eng.eta_CO(h_c, i_ud)
        z_val = eng.Z(h_c)
        return {
            "eta_co": eta,
            "z_co": z_val,
            "p_o2": eng.P_O2(h_c),
            "k_p": eng.K_P(h_c, i_ud),
            "g_v": eng.G_V(h_c, si_pig),
            "i_ud": i_ud,
            "efficiency": eta * z_val,
        }
