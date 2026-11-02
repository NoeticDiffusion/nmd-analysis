"""Truth-known gate for COMA-RESID-001 (sl_022). CPC-blind.

Constant drift: Tr(C_r) recovers the isotropic noise scale and is not
larger than matched Tr(a_raw). Neighborhood-varying mean, same isotropic
residual: Tr(a_raw) exceeds Tr(C_r). Not innovation / Ito / Family B.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from icare_v2_common import ARTICLE_DIR
from icare_v2_v301_resid_metrics import estimate_crossfit_residual_spread

DT = 4.0
NOISE_TRACE = 3.0
OUT = ARTICLE_DIR / "results" / "v3_0_1" / "resid_synthetic_gate.json"


def _simulate_constant(n: int, b: np.ndarray, *, seed: int, dt: float = DT) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = np.zeros((n, 3), dtype=float)
    for i in range(n - 1):
        x[i + 1] = x[i] + np.asarray(b, dtype=float) * dt + rng.normal(size=3) * np.sqrt(dt)
    t = np.arange(n, dtype=float) * dt
    return x, t


def _simulate_varying_mean(n_pairs: int, *, seed: int, dt: float = DT, amp: float = 1.0, omega: float = 1.5) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x_src = rng.uniform(-2.0, 2.0, size=(n_pairs, 3))
    drift = amp * np.sin(omega * x_src)
    dx = drift * dt + rng.normal(size=(n_pairs, 3)) * np.sqrt(dt)
    x = np.empty((n_pairs * 2, 3), dtype=float)
    x[0::2] = x_src
    x[1::2] = x_src + dx
    t = np.arange(n_pairs * 2, dtype=float) * dt
    segments = np.repeat(np.arange(n_pairs, dtype=np.int32), 2)
    return x, t, segments


def _check(name: str, ok: bool, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), **detail}


def main() -> int:
    rows: list[dict] = []
    b = np.array([1.0, 0.0, 0.0])
    x, t = _simulate_constant(900, b, seed=11)
    est = estimate_crossfit_residual_spread(x, t)
    med = est.get("medians") or {}
    tr_c = float(med.get("tr_c_resid", float("nan")))
    tr_a = float(med.get("tr_a_raw", float("nan")))
    rows.append(
        _check(
            "constant_drift_status_computed",
            est.get("status") == "computed",
            {"status": est.get("status"), "failure": est.get("failure_reason"), "n_valid": est.get("n_valid")},
        )
    )
    rows.append(
        _check(
            "constant_drift_tr_c_recovers_noise_scale",
            np.isfinite(tr_c) and abs(tr_c - NOISE_TRACE) < 0.45,
            {"tr_c_resid": tr_c, "target": NOISE_TRACE, "tr_a_raw": tr_a},
        )
    )
    rows.append(
        _check(
            "constant_drift_tr_a_raw_ge_tr_c",
            np.isfinite(tr_a) and np.isfinite(tr_c) and tr_a + 0.05 >= tr_c,
            {"tr_a_raw": tr_a, "tr_c_resid": tr_c},
        )
    )

    x_v, t_v, seg_v = _simulate_varying_mean(800, seed=19)
    est_v = estimate_crossfit_residual_spread(x_v, t_v, segment_id=seg_v)
    med_v = est_v.get("medians") or {}
    tr_c_v = float(med_v.get("tr_c_resid", float("nan")))
    tr_a_v = float(med_v.get("tr_a_raw", float("nan")))
    rows.append(
        _check(
            "varying_mean_status_computed",
            est_v.get("status") == "computed",
            {"status": est_v.get("status"), "failure": est_v.get("failure_reason"), "n_valid": est_v.get("n_valid")},
        )
    )
    rows.append(
        _check(
            "varying_mean_tr_a_raw_exceeds_tr_c",
            np.isfinite(tr_a_v) and np.isfinite(tr_c_v) and tr_a_v > tr_c_v * 1.15 and (tr_a_v - tr_c_v) > 0.5,
            {"tr_a_raw": tr_a_v, "tr_c_resid": tr_c_v, "ratio": (tr_c_v / tr_a_v) if tr_a_v else float("nan")},
        )
    )
    rows.append(
        _check(
            "varying_mean_tr_c_near_isotropic_residual",
            np.isfinite(tr_c_v) and abs(tr_c_v - NOISE_TRACE) < 0.8,
            {"tr_c_resid": tr_c_v, "target": NOISE_TRACE},
        )
    )

    passed = all(item["pass"] for item in rows)
    payload = {
        "gate": "COMA-RESID-001-synthetic",
        "pass": passed,
        "n_checks": len(rows),
        "estimand": "cross_fitted_residual_spread",
        "not": ["innovation", "ito", "family_b_jacobian", "ingest_transition_residual"],
        "checks": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"synthetic gate pass={passed} -> {OUT}", flush=True)
    for item in rows:
        flag = "PASS" if item["pass"] else "FAIL"
        print(f"  {flag} {item['name']}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
