"""Приёмочные сценарии v3 (без GUI)."""

from melt_dynamics import MeltDynamicsEngine


def run_scenario(name: str, h_c: float, i: float, g_t: float = 200.0, c_target: float = 0.12):
    preview = MeltDynamicsEngine.preview_free_params(h_c, i, g_t, si_pig=0.5)
    eng = MeltDynamicsEngine(
        initial_state={
            "G_metal_t": g_t,
            "C": 4.0,
            "Si": 0.5,
            "Mn": 0.3,
            "T": 1350.0,
            "FeO_slag": 12.0,
            "Si_pig": 0.5,
        },
        control_params={"h_c": h_c, "i_total": i, "target_c": c_target},
    )
    snaps = eng.run_until_target(c_target)
    last = snaps[-1] if snaps else {}
    peak_vc = max((s["v_C"] for s in snaps), default=0.0)
    t_min = last.get("t_min", 0.0)
    return {
        "name": name,
        "eta": preview["eta_co"],
        "z": preview["z_co"],
        "eff": preview["efficiency"],
        "kp": preview["k_p"],
        "gv": preview["g_v"],
        "phi": last.get("Phi", 0),
        "T": last.get("T", 0),
        "FeO": last.get("FeO_slag", 0),
        "peak_vc": peak_vc,
        "t_min": t_min,
        "steps": len(snaps),
    }


if __name__ == "__main__":
    scenarios = [
        run_scenario("soft", 2.8, 800),
        run_scenario("hard", 1.0, 1000),
        run_scenario("optimum", 2.0, 900),
    ]
    print("name\teta\tZ\teff\tK_P\tG_V\tPhi\tT\tFeO\tpeak_vC\tt_min")
    for s in scenarios:
        print(
            f"{s['name']}\t{s['eta']:.2f}\t{s['z']:.3f}\t{s['eff']:.4f}\t"
            f"{s['kp']:.0f}\t{s['gv']:.2f}\t{s['phi']:.2f}\t{s['T']:.0f}\t"
            f"{s['FeO']:.1f}\t{s['peak_vc']:.3f}\t{s['t_min']:.1f}"
        )
