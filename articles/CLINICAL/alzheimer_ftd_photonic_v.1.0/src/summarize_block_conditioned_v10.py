"""Exact-block conditioned summaries of pre-existing NDT v1.0 time series.

This reader does not refit any estimator. Values retain their recording-level
support/neighbourhoods and are only selected by the canonical block interval.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import h5py, numpy as np
from scipy.stats import mannwhitneyu

CODES = {50: "photo_5hz", 51: "photo_10hz", 52: "photo_15hz", 53: "photo_20hz"}
GROUP = {"A": "AD", "C": "Healthy", "F": "FTD"}
PRIMARY = ("log_g_max", "d_resp", "c_1")

def text(x):
    x = x[()]
    return x.decode() if isinstance(x, bytes) else str(x)

def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [])
        w.writeheader(); w.writerows(rows)

def median(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return (float(np.median(x)), len(x)) if len(x) else (float("nan"), 0)

def intervals(h5):
    b = h5["blocks"]
    out = {code: [] for code in CODES}
    for code, start, end, reason in zip(b["stage_code"][:], b["start_sec"][:], b["end_sec"][:], b["end_reason"][:]):
        if int(code) in out:
            out[int(code)].append((float(start), float(end), reason.decode() if isinstance(reason, bytes) else str(reason)))
    return out

def inside(times, pairs):
    return np.array([any(lo - 1e-6 <= t <= hi + 1e-6 for lo, hi, _ in pairs) for t in times], bool)

def rows_for(path):
    rows, qc = [], []
    with h5py.File(path, "r") as h5:
        sub = str(h5.attrs["subject_id"]); group = GROUP.get(str(h5.attrs["group"]), "Unknown")
        time = np.asarray(h5["time"][:], float); blocks = intervals(h5)
        for code, label in CODES.items():
            block_count = len(blocks[code]); window_count = int(inside(time, blocks[code]).sum())
            qc.append({"subject_id": sub, "group": group, "frequency": label, "n_blocks": block_count,
                       "n_exact_original_windows": window_count,
                       "end_reasons": ";".join(sorted({x[2] for x in blocks[code]}))})
        for horizon in (1, 2, 4):
            base = h5[f"finite_time_response/v1/primary/horizons/h{horizon}"]
            series, starts = base["series"], np.asarray(base["start_windows"][:], int)
            status = {"computation_status": text(h5["finite_time_response/v1/primary/computation_status"]),
                      "measurement_validity": text(h5["finite_time_response/v1/primary/measurement_validity"]),
                      "claim_status": text(h5["finite_time_response/v1/primary/claim_status"])}
            endpoint = starts + horizon
            for code, label in CODES.items():
                ok = (starts >= 0) & (endpoint < len(time)) & inside(time[starts.clip(0, len(time)-1)], blocks[code]) & inside(time[endpoint.clip(0, len(time)-1)], blocks[code])
                for metric in PRIMARY:
                    value, n = median(series[metric][:][ok])
                    rows.append({"subject_id": sub, "group": group, "frequency": label, "branch": "ftr_primary_3d",
                                 "horizon_steps": horizon, "metric": metric, "value": value, "n_valid_sequences": n, **status})
    return rows, qc

def bh(p):
    order=np.argsort(p); out=np.empty(len(p)); run=1.
    for rank in range(len(p),0,-1):
        i=order[rank-1]; run=min(run,p[i]*len(p)/rank); out[i]=run
    return out

def contrasts(rows):
    out=[]
    for metric in PRIMARY:
      for label in CODES.values():
        for case in ("AD","FTD"):
          a=[r["value"] for r in rows if r["branch"]=="ftr_primary_3d" and r["horizon_steps"]==2 and r["frequency"]==label and r["metric"]==metric and r["group"]==case and r["n_valid_sequences"]>=3 and np.isfinite(r["value"])]
          b=[r["value"] for r in rows if r["branch"]=="ftr_primary_3d" and r["horizon_steps"]==2 and r["frequency"]==label and r["metric"]==metric and r["group"]=="Healthy" and r["n_valid_sequences"]>=3 and np.isfinite(r["value"])]
          if len(a)>=2 and len(b)>=2:
            u,pv=mannwhitneyu(a,b,alternative="two-sided"); out.append({"frequency":label,"metric":metric,"contrast":f"{case}_vs_Healthy","n_case":len(a),"n_healthy":len(b),"median_case":float(np.median(a)),"median_healthy":float(np.median(b)),"rank_biserial":float(2*u/(len(a)*len(b))-1),"p_uncorrected":float(pv)})
    if out:
      for row,q in zip(out,bh(np.array([r["p_uncorrected"] for r in out]))): row["p_fdr_bh_primary_ftr_h2_family"]=float(q)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw-root",type=Path,required=True); ap.add_argument("--output-root",type=Path,required=True); a=ap.parse_args()
    rows=[]; qc=[]
    for path in sorted(a.raw_root.glob("sub-*/*.h5")):
        x,y=rows_for(path); rows+=x; qc+=y
    write(a.output_root/"subject_frequency_block_conditioned_v10.csv",rows); write(a.output_root/"exact_block_support_qc.csv",qc); write(a.output_root/"primary_ftr_h2_group_contrasts.csv",contrasts(rows))
    (a.output_root/"run_manifest.json").write_text(json.dumps({"analysis":"exact-block conditioned summary, not per-frequency refit","input":str(a.raw_root),"selection":"original window center inside /blocks interval; FTR endpoints in same block","primary":"3D FTR h2 log_g_max,d_resp,c_1; subject medians; >=3 sequences","secondary":"deferred: amplification series schema is unavailable for some unsupported records and must retain its own missingness contract","claim_boundary":"measurement_validity/claim status retained; no biological or per-frequency-estimator claim"},indent=2),encoding="utf-8")
if __name__=="__main__": main()
