#!/usr/bin/env python3
# make_synthetic_data.py - writes a fully synthetic data set in the same format the pipeline reads.
#
# Nothing here comes from a real test. Sample ids ITA901..ITA912 are invented (the Python tools expect the "ITA<number>"
# pattern; numbers from 900 up mark synthetic samples). The "true" plane strength is known, so you can check that the
# tools recover it:
#     TRUE_C = 10 MPa, TRUE_PHI = 22 deg, plus a random scatter of the peak deviatoric stress.
#
# Usage (from this folder):
#     python make_synthetic_data.py
# Output: specimens.csv, targets.csv, curves_lab.csv (same folder)
import math
import numpy as np
import pandas as pd

TRUE_C = 10.0       # MPa
TRUE_PHI = 22.0     # deg
SCATTER = 0.06      # relative scatter of the peak (1 sigma)
rng = np.random.default_rng(2027)

# id, sigma3 (MPa), dip (deg), failure mode, confidence, use in plane fit
SAMPLES = [
    ("ITA901", 3.0, 28.0, "foliation", "high", "yes"),
    ("ITA902", 3.0, 41.0, "foliation", "high", "yes"),
    ("ITA903", 6.0, 33.0, "foliation", "high", "yes"),
    ("ITA904", 6.0, 47.0, "foliation", "medium", "yes"),
    ("ITA905", 6.0, 58.0, "foliation", "high", "yes"),
    ("ITA906", 12.0, 36.0, "foliation", "medium", "yes"),
    ("ITA907", 12.0, 52.0, "foliation", "high", "yes"),
    ("ITA908", 12.0, 44.0, "foliation", "medium", "yes"),
    ("ITA909", 24.0, 40.0, "foliation", "high", "yes"),
    ("ITA910", 24.0, 63.0, "foliation", "medium", "yes"),
    ("ITA911", 12.0, 0.0, "matrix", "high", "no"),
    ("ITA912", 24.0, 38.0, "mixed", "low", "check"),
]

TARGET_COLS = ["id_ita", "sheet", "in_analysis", "in_flow", "failure_mode", "use_plane_fit", "confidence", "tab_group",
               "sigma3_target_MPa", "sigma3_at_peak_MPa", "dev_peak_MPa", "sigma1_peak_MPa", "eps_ax_peak_pct",
               "eps_rad_peak_pct", "eps_vol_peak_pct", "time_to_peak_s", "E_manual_GPa", "E_fit_40_60_GPa",
               "E_manual_over_fit", "nu_manual", "nu_fit_40_60", "dev_residual_auto_MPa", "residual_over_peak",
               "residual_window_rel_spread", "residual_status_visual", "dev_residual_ppt_MPa", "eps_ax_at_residual_pct",
               "anisotropy_angle_deg", "beta_plane_to_axis_deg", "sigma_n_plane_MPa", "tau_plane_MPa",
               "stage2_axial_strain_rate_pct_per_s", "peak_reliable", "eps_peak_reliable"]
CURVE_COLS = ["id_ita", "in_analysis", "xl_row", "idx", "phase", "test_stage", "t_s", "t_rel_s", "ax_disp_mm",
              "ax_force_kN", "extenso_A_mm", "extenso_B_mm", "circ_extenso_mm", "conf_MPa", "dev_MPa", "sigma1_MPa",
              "eps_ax_pct", "eps_rad_pct", "eps_vol_pct", "E_inst_GPa", "nu_inst", "qc_flag"]

RATE = 0.0005       # axial strain rate, %/s (same order as a slow lab test)


def peak_deviator(s3, dip):
    th = math.radians(dip)
    t = math.tan(math.radians(TRUE_PHI))
    return (TRUE_C + s3 * t) / (math.sin(th) * math.cos(th) - math.cos(th) ** 2 * t)


def curve(sid, s3, D, E_gpa, nu, eps_pk, res_ratio, fol):
    """Elastic branch, rounded peak, then a drop to a residual plateau (all synthetic)."""
    rows = []
    n_pre, n_post = 260, 120
    e_end = eps_pk * (1.0 + 0.9)
    eps = np.concatenate([np.linspace(0, eps_pk, n_pre), np.linspace(eps_pk, e_end, n_post)[1:]])
    for i, e in enumerate(eps):
        if e <= eps_pk:
            x = e / eps_pk
            d = D * (1.0 - (1.0 - x) ** 2.2) if x < 1 else D
            d = min(d, E_gpa * 1000.0 * e / 100.0)
            d = D * (x * (2 - x)) if x < 1 else D
        else:
            y = (e - eps_pk) / (e_end - eps_pk)
            d = D - (D - res_ratio * D) * (1.0 - math.exp(-6.0 * y)) if fol else D * (1.0 - 0.15 * y)
        rows.append(dict(id_ita=sid, in_analysis="yes", xl_row=i + 2, idx=i, phase="pre" if e <= eps_pk else "post",
                         test_stage=2, t_s=e / RATE, t_rel_s=(e - eps_pk) / RATE, ax_disp_mm=e / 100.0 * 128.15,
                         ax_force_kN=d * math.pi * 32.0 ** 2 / 1000.0, extenso_A_mm=e / 100.0 * 60.0,
                         extenso_B_mm=e / 100.0 * 60.0, circ_extenso_mm=-nu * e / 100.0 * 2 * math.pi * 32.0,
                         conf_MPa=s3, dev_MPa=d, sigma1_MPa=s3 + d, eps_ax_pct=e, eps_rad_pct=-nu * e,
                         eps_vol_pct=e * (1 - 2 * nu), E_inst_GPa=E_gpa, nu_inst=nu, qc_flag=""))
    return rows


def main():
    spec, tgt, cur = [], [], []
    for sid, s3, dip, mode, conf, fit in SAMPLES:
        if mode == "matrix":
            D = 160.0 * (1 + 0.012 * s3)
            res = 0.85
        elif mode == "mixed":
            D = peak_deviator(s3, dip) * 1.25
            res = 0.55
        else:
            D = peak_deviator(s3, dip)
            res = 0.45
        D *= float(np.exp(rng.normal(0.0, SCATTER)))
        E = float(rng.uniform(20.0, 28.0)) if mode != "matrix" else 42.0
        nu = float(rng.uniform(0.25, 0.4))
        eps_pk = D / (E * 1000.0) * 100.0 * 1.25
        th = math.radians(dip)
        sn = s3 + D * math.cos(th) ** 2
        tau = D * math.sin(th) * math.cos(th)
        t = {c: "" for c in TARGET_COLS}
        t.update(id_ita=sid, in_analysis="yes", in_flow="yes", failure_mode=mode, use_plane_fit=fit, confidence=conf,
                 sigma3_target_MPa=s3, sigma3_at_peak_MPa=s3, dev_peak_MPa=round(D, 3), sigma1_peak_MPa=round(s3 + D, 3),
                 eps_ax_peak_pct=round(eps_pk, 4), E_fit_40_60_GPa=round(E, 2), nu_fit_40_60=round(nu, 3),
                 dev_residual_auto_MPa=round(res * D, 3), residual_over_peak=res,
                 anisotropy_angle_deg=dip, beta_plane_to_axis_deg=90.0 - dip, sigma_n_plane_MPa=round(sn, 3),
                 tau_plane_MPa=round(tau, 3), peak_reliable="yes", eps_peak_reliable="yes")
        tgt.append(t)
        spec.append(dict(id_ita=sid, in_analysis="yes", in_flow="yes", failure_mode=mode, use_plane_fit=fit,
                         confidence=conf, sigma3_nominal_MPa=s3, dev_peak_MPa=round(D, 3), anisotropy_angle_deg=dip,
                         diameter_mm=64.0, height_mm=128.15))
        cur += curve(sid, s3, D, E, nu, eps_pk, res, mode != "matrix")
    pd.DataFrame(spec).to_csv("specimens.csv", index=False)
    pd.DataFrame(tgt, columns=TARGET_COLS).to_csv("targets.csv", index=False)
    pd.DataFrame(cur, columns=CURVE_COLS).to_csv("curves_lab.csv", index=False, float_format="%.6g")
    print("wrote specimens.csv, targets.csv, curves_lab.csv (%d samples, %d curve rows)" % (len(SAMPLES), len(cur)))
    print("true plane strength: c = %.1f MPa, phi = %.1f deg" % (TRUE_C, TRUE_PHI))


if __name__ == "__main__":
    main()
