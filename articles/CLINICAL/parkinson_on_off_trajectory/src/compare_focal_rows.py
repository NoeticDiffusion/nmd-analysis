"""Compare focal rows from new bundle against published values."""
from __future__ import annotations
import pandas as pd
from pathlib import Path

RESULTS_NEW = Path(__file__).resolve().parents[1] / "results" / "parkinson_on_off_dual_contract_20260608"
RESULTS_OLD = Path(__file__).resolve().parents[1] / "results" / "parkinson_on_off_dual_contract_20260602"

# Published focal rows: (label, contrast, layer, filters, pub_lmed, pub_rmed, pub_d, pub_q)
PUB = [
    ("1.frontal d_n_std OFF",   "Control_vs_Parkinson_OFF",  "std",
     dict(analysis_type="regional_9d", network="frontal", metric="d_n_std"),
     0.852, 0.530, -1.268, 0.013),
    ("2.global d_n_std OFF",    "Control_vs_Parkinson_OFF",  "std",
     dict(analysis_type="global_mnps_9d", metric="d_n_std"),
     0.912, 0.505, -1.194, 0.013),
    ("3.speed_median 3D OFF",   "Control_vs_Parkinson_OFF",  "evt",
     dict(segment_label="eyes_closed", metric="speed_median", dims=3),
     0.105, 0.078, -1.212, 0.0025),
    ("4.noetic_act_kin 9D OFF", "Control_vs_Parkinson_OFF",  "evt",
     dict(segment_label="eyes_closed", metric="noetic_action_kinetic", dims=9),
     0.0328, 0.0164, -1.085, 0.0050),
    ("5.mdr_median 9D ON",      "Control_vs_Parkinson_ON",   "std",
     dict(analysis_type="global_mnps_jacobian_9d", metric="mdr_median"),
     0.115, 0.134, 1.478, 0.0095),
    ("6.hysteresis novel ON",   "Control_vs_Parkinson_ON",   "evt",
     dict(segment_label="novel_tone", metric="hysteresis_area_me"),
     0.0890, 0.0484, -1.039, 0.0269),
    ("7.signed_div OFF_vs_ON",  "Parkinson_OFF_vs_ON",       "std",
     dict(analysis_type="tier2_jacobian", metric="signed_divergence_balance_mean_neg"),
     -0.0440, -0.0503, -0.711, 0.044),
]


def lookup(df: pd.DataFrame, contrast: str, filters: dict) -> pd.Series | None:
    mask = df["contrast_name"] == contrast
    for col, val in filters.items():
        if col in df.columns:
            mask = mask & (df[col] == val)
    rows = df[mask]
    return rows.iloc[0] if not rows.empty else None


def run(results_dir: Path, label: str) -> None:
    std = pd.read_csv(results_dir / "primary_standard_contrasts.csv")
    evt = pd.read_csv(results_dir / "primary_event_contrasts.csv")

    n05_std = (std["q_value"] < 0.05).sum()
    n10_std = (std["q_value"] < 0.1).sum()
    n05_evt = (evt["q_value"] < 0.05).sum()
    n10_evt = (evt["q_value"] < 0.1).sum()
    print(f"\n=== {label} ===")
    print(f"Retained: std q<0.05={n05_std}, q<0.1={n10_std} | evt q<0.05={n05_evt}, q<0.1={n10_evt}")
    print(f"Published: std q<0.05=30, q<0.1=63 | evt q<0.05=12, q<0.1=18")
    print()
    print(f"{'Row':<26} {'d_new':>7} {'d_pub':>7} {'Dd':>7}  {'q_new':>8} {'q_pub':>7} {'Dq':>8}  notes")
    print("-" * 90)
    for name, contrast, layer, filt, plm, prm, pd_, pq in PUB:
        df = std if layer == "std" else evt
        r = lookup(df, contrast, filt)
        if r is None:
            print(f"{name:<26} {'MISSING'}")
            continue
        d = float(r["effect_size"])
        q = float(r["q_value"])
        dd = d - pd_
        dq = q - pq
        notes = []
        if abs(dd) > 0.02:
            notes.append(f"d-DIFF({dd:+.3f})")
        if abs(dq) > 0.005:
            notes.append(f"q-DIFF({dq:+.5f})")
        if q > 0.05 >= pq:
            notes.append("*** NO LONGER q<0.05 ***")
        elif q <= 0.05 < pq:
            notes.append("(newly passes)")
        print(f"{name:<26} {d:>7.3f} {pd_:>7.3f} {dd:>+7.3f}  {q:>8.5f} {pq:>7.5f} {dq:>+8.5f}  {' '.join(notes)}")


def extra_rows(results_dir: Path) -> None:
    std = pd.read_csv(results_dir / "primary_standard_contrasts.csv")
    retained = std[std["q_value"] < 0.05].copy()
    print("\n=== Standard rows q<0.05 (new bundle, top by |d|) ===")
    retained["abs_d"] = retained["effect_size"].abs()
    cols = ["contrast_name", "analysis_type", "network", "metric", "left_median", "right_median", "effect_size", "q_value"]
    print(retained.sort_values("abs_d", ascending=False)[cols].head(20).to_string(index=False))


if __name__ == "__main__":
    run(RESULTS_NEW, "NEW BUNDLE 20260608")
    extra_rows(RESULTS_NEW)
    if RESULTS_OLD.exists():
        run(RESULTS_OLD, "OLD BUNDLE 20260602")
