"""Truth-known gate for COMA-DDC-001 (sl_008). CPC-blind."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from icare_v2_common import ARTICLE_DIR
from icare_v2_v301_ddc_metrics import coupling_metrics, estimate_crossfit_coupling

EPS = 1e-12
DT = 4.0
OUT = ARTICLE_DIR / "results" / "v3_0_1" / "ddc_synthetic_gate.json"


def _rot(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1
    return q


def _along_tensor(u: np.ndarray, par: float, perp: float) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    u = u / np.linalg.norm(u)
    p = np.eye(3) - np.outer(u, u)
    return (par**2) * np.outer(u, u) + (perp**2) * p


def _transverse_sheet(u: np.ndarray, lam: float) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    u = u / np.linalg.norm(u)
    return lam * (np.eye(3) - np.outer(u, u))


def _transverse_line(u: np.ndarray, v: np.ndarray, lam: float) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    v = v - u * np.dot(v, u)
    v = v / np.linalg.norm(v)
    return lam * np.outer(v, v)


def _simulate(n: int, b: np.ndarray, a: np.ndarray, *, seed: int, dt: float = DT) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    chol = np.linalg.cholesky(0.5 * (a + a.T) + 1e-10 * np.eye(3))
    x = np.zeros((n, 3), dtype=float)
    for i in range(n - 1):
        x[i + 1] = x[i] + np.asarray(b, dtype=float) * dt + chol @ rng.normal(size=3) * np.sqrt(dt)
    t = np.arange(n, dtype=float) * dt
    return x, t


def _check(name: str, ok: bool, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), **detail}


def main() -> int:
    b = np.array([1.0, 0.0, 0.0])
    rows: list[dict] = []

    iso = coupling_metrics(b, np.eye(3), dt=DT)
    rows.append(_check("isotropic_F_perp_2_3", abs(iso["f_perp"] - 2.0 / 3.0) < 1e-10, iso))

    along = coupling_metrics(b, _along_tensor(b, 3.0, 0.3), dt=DT)
    rows.append(_check("elongated_along_reduces_F_perp", along["f_perp"] < iso["f_perp"] - 0.2, along))

    across = coupling_metrics(b, _along_tensor(b, 0.3, 3.0), dt=DT)
    rows.append(_check("elongated_orthogonal_increases_F_perp", across["f_perp"] > iso["f_perp"] + 0.2, across))

    sheet = coupling_metrics(b, _transverse_sheet(b, 1.0), dt=DT)
    rows.append(_check("transverse_sheet_d_perp_2", abs(sheet["d_perp_eff"] - 2.0) < 1e-8, sheet))

    line = coupling_metrics(b, _transverse_line(b, np.array([0.0, 1.0, 0.0]), 1.0), dt=DT)
    rows.append(_check("transverse_line_d_perp_1", abs(line["d_perp_eff"] - 1.0) < 1e-8, line))

    zero_b = coupling_metrics(np.zeros(3), np.eye(3), dt=DT)
    rows.append(
        _check(
            "zero_b_directional_nan_ratio_zero",
            not np.isfinite(zero_b["f_perp"]) and abs(zero_b["r_ba"] - 0.0) < 1e-12,
            zero_b,
        )
    )

    q = _rot(7)
    scale = 3.0
    rotated = coupling_metrics(scale * q @ b, (scale**2) * q @ np.eye(3) @ q.T, dt=DT)
    rows.append(
        _check(
            "rotation_and_scalar_invariance",
            abs(rotated["f_perp"] - iso["f_perp"]) < 1e-10
            and abs(rotated["d_perp_eff"] - iso["d_perp_eff"]) < 1e-10
            and abs(rotated["r_ba"] - iso["r_ba"]) < 1e-10,
            {"iso": iso, "rotated": rotated},
        )
    )

    iso_adom = iso["a_dom"]
    along_adom = coupling_metrics(b, _along_tensor(b, 3.0, 0.3), dt=DT)["a_dom"]
    across_adom = coupling_metrics(b, _along_tensor(b, 0.3, 3.0), dt=DT)["a_dom"]
    rows.append(_check("isotropic_A_dom_1", abs(iso_adom - 1.0) < 1e-10, {"a_dom": iso_adom}))
    rows.append(_check("along_A_dom_near_1", along_adom > 0.95, {"a_dom": along_adom}))
    rows.append(_check("orthogonal_A_dom_small", across_adom < 0.2, {"a_dom": across_adom}))
    rotated_adom = coupling_metrics(scale * q @ b, (scale**2) * q @ _along_tensor(b, 0.3, 3.0) @ q.T, dt=DT)["a_dom"]
    rows.append(_check("A_dom_rotation_scalar_invariance", abs(rotated_adom - across_adom) < 1e-10, {"base": across_adom, "rotated": rotated_adom}))

    x, t = _simulate(900, b, np.eye(3), seed=11)
    est = estimate_crossfit_coupling(x, t)
    rows.append(
        _check(
            "estimator_recovers_isotropic_F_perp",
            est.get("status") == "computed" and abs(est["medians"]["f_perp"] - 2.0 / 3.0) < 0.08,
            {"status": est.get("status"), "medians": est.get("medians"), "n_valid": est.get("n_valid")},
        )
    )
    x_r = scale * (x @ q.T)
    est_r = estimate_crossfit_coupling(x_r, t)
    rows.append(
        _check(
            "estimator_rotation_scalar_invariance",
            est.get("status") == "computed"
            and est_r.get("status") == "computed"
            and abs(est["medians"]["f_perp"] - est_r["medians"]["f_perp"]) < 0.04
            and abs(est["medians"]["r_ba"] - est_r["medians"]["r_ba"]) < 0.08,
            {"base": est.get("medians"), "rotated": est_r.get("medians")},
        )
    )

    x_along, t_along = _simulate(900, b, _along_tensor(b, 3.0, 0.3), seed=13)
    est_along = estimate_crossfit_coupling(x_along, t_along)
    x_across, t_across = _simulate(900, b, _along_tensor(b, 0.3, 3.0), seed=17)
    est_across = estimate_crossfit_coupling(x_across, t_across)
    rows.append(
        _check(
            "estimator_along_vs_across_F_perp",
            est_along.get("status") == "computed"
            and est_across.get("status") == "computed"
            and est_along["medians"]["f_perp"] < est["medians"]["f_perp"]
            and est_across["medians"]["f_perp"] > est["medians"]["f_perp"],
            {
                "iso": est.get("medians"),
                "along": est_along.get("medians"),
                "across": est_across.get("medians"),
            },
        )
    )

    passed = all(item["pass"] for item in rows)
    payload = {"gate": "COMA-DDC-001-synthetic", "pass": passed, "n_checks": len(rows), "checks": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"synthetic gate pass={passed} -> {OUT}", flush=True)
    for item in rows:
        flag = "PASS" if item["pass"] else "FAIL"
        print(f"  {flag} {item['name']}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
