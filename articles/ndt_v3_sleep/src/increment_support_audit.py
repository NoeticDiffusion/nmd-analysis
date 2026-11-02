"""Fail-closed structural audit of the accepted diffusion candidate increments."""
from __future__ import annotations
import csv, hashlib, json, platform, importlib.metadata
from pathlib import Path
from typing import Any
import h5py
import numpy as np
import yaml

KNOWN = {0, 1, 2, 3, 4}
REQUIRED_MANIFEST_STATUS = "candidate_only_membership_exported"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def _str(x):
    return x.decode() if isinstance(x, (bytes, np.bytes_)) else str(x)

def _vec(f, name):
    a = np.asarray(f[name][()])
    return a.reshape(-1)

def _read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))

def _f(x): return float(x)
def _i(x):
    if isinstance(x, str): return int(x)
    if not np.isfinite(x) or x != int(x): raise ValueError('noninteger ID or stage')
    return int(x)

def _bool(x):
    if str(x).lower() not in ('true', 'false', '1', '0'): raise ValueError('invalid boolean')
    return str(x).lower() in ('true', '1')

def audit_rows(rows, h5, nominal_dt: float, max_rel_dt: float):
    ids = _vec(h5, "/epoch_id"); starts = _vec(h5, "/window_start"); ends = _vec(h5, "/window_end")
    times = _vec(h5, "/time"); stages = np.array([_i(x) for x in _vec(h5, "/labels/stage")])
    raw = _vec(h5, "/row_source/raw_file")
    coords = np.asarray(h5["/coords_3d_subject_anchored/values"][()])
    by_id = {_i(v): i for i, v in enumerate(ids)}
    if any(len(a) != len(ids) for a in (starts, ends, times, stages, raw, coords)) or coords.shape != (len(ids), 3): raise ValueError('H5 array shape mismatch')
    if not np.isfinite(nominal_dt) or nominal_dt <= 0 or not np.isfinite(max_rel_dt) or max_rel_dt < 0: raise ValueError('invalid dt policy')
    if len(by_id) != len(ids): raise ValueError("H5 epoch_id is not unique")
    out = []
    seen = set(); selected = set()
    for r in rows:
        q, s, t = _i(r["query_epoch_id"]), _i(r["source_epoch_id"]), _i(r["target_epoch_id"])
        if q not in by_id or s not in by_id or t not in by_id: raise ValueError("candidate references unknown epoch_id")
        qi, si, ti = by_id[q], by_id[s], by_id[t]
        key = (q, _i(r["selection_index"]))
        if key in seen or (q, s) in selected or key[1] < 0: raise ValueError("duplicate query selection")
        seen.add(key); selected.add((q, s))
        for role, i in (("query", qi), ("source", si), ("target", ti)):
            if _i(r[f'{role}_index']) != i: raise ValueError('candidate index disagrees with H5')
            for suffix, expected in (('start', starts[i]), ('end', ends[i])):
                actual = float(r[f'{role}_window_{suffix}'])
                if actual != expected and not (np.isnan(actual) and np.isnan(expected)): raise ValueError('candidate bound disagrees with H5')
        for col, expected in (("query_stage_code", stages[qi]), ("source_stage_code", stages[si]), ("target_stage_code", stages[ti])):
            if _i(r[col]) != int(expected): raise ValueError(f"candidate {col} disagrees with H5")
        for col, expected in (("query_stage_unknown", stages[qi] not in KNOWN), ("source_stage_unknown", stages[si] not in KNOWN), ("target_stage_unknown", stages[ti] not in KNOWN)):
            if _bool(r[col]) != bool(expected): raise ValueError(f"candidate {col} disagrees with H5")
        checks = {
            "indices_exact": (_i(r["query_index"]) == qi and _i(r["source_index"]) == si and _i(r["target_index"]) == ti),
            "source_target_consecutive": ti == si + 1 and int(ids[ti]) == int(ids[si]) + 1,
            "same_raw_file": bool(_str(raw[si])) and _str(raw[si]) == _str(raw[ti]),
            "finite_endpoints": bool(np.isfinite(coords[si]).all() and np.isfinite(coords[ti]).all()),
            "finite_time_bounds": bool(np.isfinite(times[[qi, si, ti]]).all() and np.isfinite(starts[[si, ti]]).all() and np.isfinite(ends[[si, ti]]).all()),
            "valid_window_bounds": bool(ends[si] > starts[si] and ends[ti] > starts[ti]),
            "touching_windows": bool(ends[si] == starts[ti]),
            "dt_positive": bool(times[ti] - times[si] > 0),
            "dt_exact": bool(_f(r["dt_sec"]) == float(times[ti] - times[si])),
        }
        dt = float(times[ti] - times[si])
        checks["dt_within_stored_limit"] = bool(np.isfinite(dt) and abs(dt - nominal_dt) / nominal_dt <= max_rel_dt)
        structural = all(checks.values())
        qst, sst, tst = int(stages[qi]), int(stages[si]), int(stages[ti])
        q_known, s_known, t_known = qst in KNOWN, sst in KNOWN, tst in KNOWN
        same_query_stage = bool(q_known and s_known and t_known and sst == qst and tst == qst)
        out.append({**r, **{k: int(v) for k, v in checks.items()},
                    "structurally_admissible": int(structural), "same_known_stage": int(same_query_stage),
                    "query_stage_h5": qst, "source_stage_h5": sst, "target_stage_h5": tst,
                    "query_stage_unknown_h5": int(not q_known), "source_stage_unknown_h5": int(not s_known),
                    "target_stage_unknown_h5": int(not t_known),
                    "full_support_status": "not_assessed"})
    return out


def build_pool(h5, nominal_dt, max_rel_dt):
    """All adjacent H5 rows, including structurally invalid and unknown pairs."""
    ids = _vec(h5, '/epoch_id'); stage = _vec(h5, '/labels/stage')
    starts = _vec(h5, '/window_start'); ends = _vec(h5, '/window_end'); times = _vec(h5, '/time')
    rows = []
    for s in range(len(ids) - 1):
        r = {'selection_index': 0, 'dt_sec': times[s+1] - times[s]}
        for role, i in (('query', s), ('source', s), ('target', s+1)):
            r.update({f'{role}_epoch_id': ids[i], f'{role}_index': i,
                      f'{role}_stage_code': stage[i], f'{role}_stage_unknown': stage[i] not in KNOWN,
                      f'{role}_window_start': starts[i], f'{role}_window_end': ends[i]})
        rows.append(r)
    audited = audit_rows(rows, h5, nominal_dt, max_rel_dt)
    return [{**{k:v for k,v in r.items() if not k.startswith('query') and k not in ('selection_index', 'same_known_stage')},
             'same_known_endpoint_stage': r['same_known_stage'],
             'annotation_eligible': int(r['same_known_stage'] and r['structurally_admissible']),
             'touches_code8': int(r['source_stage_h5'] == 8 or r['target_stage_h5'] == 8)} for r in audited]

def _write_csv(path, rows):
    if not rows: raise ValueError("refusing empty audit table")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def run(config_path: str | Path):
    cfgp = Path(config_path).resolve(); config_hash = sha256(cfgp)
    cfg = yaml.safe_load(cfgp.read_text(encoding="utf-8"))
    required = {"input_h5", "candidate_manifest", "candidate_neighbors", "candidate_query_support", "policy", "analysis_code"}
    pins = cfg.get("pins", {})
    if set(pins) != required: raise ValueError("pins must contain exactly all required inputs and runner")
    paths = {k: Path(cfg[k]).resolve() for k in required}
    if paths['analysis_code'] != Path(__file__).resolve(): raise ValueError('runner identity mismatch')
    before = {k: sha256(p) for k,p in paths.items()}
    if any(before[k] != str(pins[k]).lower() for k in required): raise ValueError('input/code/policy hash mismatch')
    out = Path(cfg['output_root']).resolve()
    if out.exists(): raise FileExistsError('output must be a new directory')
    manifest = json.loads(paths['candidate_manifest'].read_text(encoding='utf-8'))
    if manifest.get('status') != REQUIRED_MANIFEST_STATUS: raise ValueError('candidate status mismatch')
    for k,v in {'claim_status':'no_biological_claim','historical_membership_status':'not_claimed','full_support_status':'not_assessed'}.items():
        if manifest.get(k) != v: raise ValueError('candidate qualification mismatch')
    gate_keys = ('computation_status_computed','input_h5_stable_after_all_usage','input_h5_stable_before_after','producer_files_stable_after_all_usage','producer_files_stable_before_after','selected_covariance_algebra_exact','settings_match_stored_provenance','support_count_exact','tensor_exact_after_stored_dtype_cast','valid_exact')
    if any(manifest.get('gate',{}).get(k) is not True for k in gate_keys): raise ValueError('candidate gate mismatch')
    if manifest.get('input_h5_sha256') != before['input_h5']: raise ValueError('candidate H5 identity mismatch')
    rows = _read_rows(paths['candidate_neighbors']); prior_queries = _read_rows(paths['candidate_query_support'])
    with h5py.File(paths['input_h5'],'r') as h5:
        base='/dynamical_families/diffusion/v1/'
        nominal=float(h5[base+'summary/nominal_dt_sec'][()])
        maxrel=float(h5[base+'provenance/settings/max_dt_relative_deviation'][()])
        k=_i(h5[base+'provenance/settings/neighborhood_k'][()])
        if cfg['nominal_dt_sec'] != nominal or cfg['max_dt_relative_deviation'] != maxrel or k < 1: raise ValueError('dt policy mismatch with stored provenance')
        times=_vec(h5,'/time'); x=np.asarray(h5['/coords_3d_subject_anchored/values'][()]); ids=_vec(h5,'/epoch_id')
        expected_ids={_i(v) for v in ids[np.isfinite(times)&np.isfinite(x).all(axis=1)]}
        pool=build_pool(h5,nominal,maxrel)
        audited=audit_rows(rows,h5,nominal,maxrel)
    if any(not r['dt_exact'] for r in audited): raise ValueError('candidate dt disagrees with H5')
    grouped={}
    for r in audited: grouped.setdefault(_i(r['query_epoch_id']),[]).append(r)
    if set(grouped) != expected_ids: raise ValueError('candidate query coverage mismatch')
    prior={_i(r['query_epoch_id']):r for r in prior_queries}
    if set(prior)!=expected_ids or len(prior_queries)!=len(prior): raise ValueError('candidate query summary identity mismatch')
    queries=[]
    for q,part in sorted(grouped.items()):
        if {_i(r['selection_index']) for r in part}!=set(range(k)): raise ValueError('candidate neighbor count mismatch')
        unknown=bool(part[0]['query_stage_unknown_h5']); same=sum(r['same_known_stage'] for r in part)
        if _bool(prior[q]['query_stage_known'])!=(not unknown): raise ValueError('candidate known status mismatch')
        if not unknown and _i(prior[q]['same_known_stage_source_target_count'])!=same: raise ValueError('candidate endpoint count mismatch')
        queries.append({'query_epoch_id':q,'stage_code':part[0]['query_stage_h5'],'neighbor_count':len(part),'structurally_admissible_count':sum(r['structurally_admissible'] for r in part),'stage_only_eligible_count':None if unknown else sum(int(r['same_known_stage'] and r['structurally_admissible']) for r in part),'full_qualified_count':None,'full_support_status':'not_assessed'})
    counts=[]
    for code in sorted(KNOWN | {r['source_stage_h5'] for r in pool}):
        selected=[r for r in pool if r['source_stage_h5']==code]
        counts.append({'stage_code':code,'all_adjacent_source_rows':len(selected),'structurally_admissible_rows':sum(r['structurally_admissible'] for r in selected),'same_known_endpoint_rows':sum(r['annotation_eligible'] for r in selected),'full_qualified_rows':None,'full_support_status':'not_assessed'})
    after={key:sha256(path) for key,path in paths.items()}
    if before!=after or config_hash!=sha256(cfgp): raise ValueError('input/code/config changed during audit')
    out.mkdir(parents=True,exist_ok=False)
    for name,table in [('increment_rows.csv',audited),('all_adjacent_pool.csv',pool),('pool_stage_counts.csv',counts),('query_support_summary.csv',queries)]: _write_csv(out/name,table)
    report={'schema_version':'ndt_v3_sleep.increment_support_audit.v1','status':'audited','claim_status':'no_biological_claim','historical_membership_status':'not_claimed','feature_filter_support_status':'not_assessed','neighborhood_stage_purity_status':'not_assessed','full_qualified_rows':None,'all_adjacent_pool_count':len(pool),'pool_structural_count':sum(r['structurally_admissible'] for r in pool),'pool_same_known_endpoint_count':sum(r['annotation_eligible'] for r in pool),'pool_code8_endpoint_count':sum(r['touches_code8'] for r in pool),'candidate_row_count':len(audited),'candidate_structural_count':sum(r['structurally_admissible'] for r in audited),'candidate_stage_only_eligible_count':sum(int(r['same_known_stage'] and r['structurally_admissible']) for r in audited),'nominal_dt_sec':nominal,'max_dt_relative_deviation':maxrel,'inputs':{key:str(path) for key,path in paths.items()},'input_hashes_before':before,'input_hashes_after':after,'config':str(cfgp),'config_sha256':config_hash,'runtime':{'python':platform.python_version(),'packages':{n:importlib.metadata.version(n) for n in ('numpy','h5py','PyYAML')}}}
    (out/'audit_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    index=out/'output_hashes.json'
    index.write_text(json.dumps({p.name:sha256(p) for p in out.iterdir() if p.is_file()},indent=2,sort_keys=True),encoding='utf-8')
    (out/'output_hashes.sha256').write_text(sha256(index)+'  output_hashes.json\n',encoding='utf-8')
    return report

if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--config", required=True); a=ap.parse_args(); print(json.dumps(run(a.config), indent=2))
