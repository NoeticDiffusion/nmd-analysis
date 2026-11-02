"""Truth-known gate for COMA-HORIZON-001 (sl_027). CPC-blind.

Isotropic random-walk increments: Tr(C_h) grows with h and d_eff stays near 3.
This is not a diffusion claim; it only checks that common-support C_h sees
horizon growth when the generating process actually has it.
"""
from __future__ import annotations

import json

import numpy as np

from icare_v2_common import ARTICLE_DIR
from icare_v2_v301_horizon_metrics import estimate_horizon_geometry

DT = 4.0
OUT = ARTICLE_DIR / "results" / "v3_0_1" / "horizon_synthetic_gate.json"


def _simulate_rw(n: int, *, seed: int, dt: float = DT) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = np.cumsum(rng.normal(size=(n, 3)), axis=0)
    t = np.arange(n, dtype=float) * dt
    return x, t


def _check(name: str, ok: bool, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), **detail}


def main() -> int:
    x, t = _simulate_rw(900, seed=23)
    est = estimate_horizon_geometry(x, t)
    med = est.get("medians") or {}
    tr2 = float(med.get("cs_tr_h2", float("nan")))
    tr4 = float(med.get("cs_tr_h4", float("nan")))
    tr8 = float(med.get("cs_tr_h8", float("nan")))
    de2 = float(med.get("cs_d_eff_h2", float("nan")))
    ratio82 = float(tr8 / tr2) if np.isfinite(tr2) and tr2 > 0 and np.isfinite(tr8) else float("nan")
    rows = [
        _check(
            "status_computed",
            est.get("status") == "computed",
            {"status": est.get("status"), "failure": est.get("failure_reason"), "n_valid_cs": est.get("n_valid_cs")},
        ),
        _check(
            "trace_grows_with_horizon",
            np.isfinite(tr2) and np.isfinite(tr4) and np.isfinite(tr8) and tr2 < tr4 < tr8,
            {"cs_tr_h2": tr2, "cs_tr_h4": tr4, "cs_tr_h8": tr8},
        ),
        _check(
            "trace_ratio_near_lag_ratio",
            np.isfinite(ratio82) and 2.5 <= ratio82 <= 5.5,
            {"tr8_over_tr2": ratio82, "target": 4.0},
        ),
        _check(
            "shape_near_isotropic",
            np.isfinite(de2) and de2 > 2.4,
            {"cs_d_eff_h2": de2, "target": 3.0},
        ),
    ]
    payload = {
        "gate": "COMA-HORIZON-001-synthetic",
        "pass": all(row["pass"] for row in rows),
        "n_checks": len(rows),
        "estimand": "empirical_finite_horizon_increment_geometry",
        "not": ["diffusion_coefficient", "family_b_jacobian", "generator", "C_h_over_hdt_as_primary"],
        "checks": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"pass={payload['pass']} wrote {OUT}", flush=True)
    for row in rows:
        print(f"  {row['name']}: {row['pass']}", flush=True)
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
