"""Frozen two-participant descriptive direction check; no statistical inference."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math

COORDS = {"3d": ("m", "d", "e"), "9d": ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise ValueError("duplicate JSON key")
            out[key] = value
        return out
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))

def contrasts(summary):
    if summary.get("scientific_qualification") != "not_assessed": raise ValueError("qualification mismatch")
    out = {}
    for rep, names in COORDS.items():
        rows = summary["representations"][rep]["summary"]
        for name in names:
            coordinate = f"mnps_{rep}_{name}"
            selected = {}
            for stage in (0, 2):
                found = [r for r in rows if r["coordinate"] == coordinate and r["stage_code"] == stage]
                if len(found) != 1: raise ValueError("missing or duplicate contrast coordinate")
                row = found[0]
                n = row["n"]
                if isinstance(n, bool) or not isinstance(n, int) or n < 0: raise ValueError("invalid denominator")
                median = row["median"]
                if n > 0 and (median is None or isinstance(median, bool) or not math.isfinite(median)): raise ValueError("invalid supported median")
                if n == 0 and median is not None: raise ValueError("empty group must remain null")
                selected[stage] = row
            valid = all(selected[s]["n"] > 0 for s in (0, 2))
            delta = selected[2]["median"] - selected[0]["median"] if valid else None
            if delta is not None and not math.isfinite(delta): raise ValueError("nonfinite contrast")
            out[(rep, coordinate)] = {"n_wake": selected[0]["n"], "n_n2": selected[2]["n"],
                "n2_minus_wake_median": delta, "direction": None if delta is None else (1 if delta > 0 else -1 if delta < 0 else 0)}
    return out

def run(reference, candidate, protocol, participants, output):
    paths = [Path(x).resolve() for x in (reference, candidate, protocol, participants)]
    pins = {str(p): sha(p) for p in paths}
    if pins[str(paths[2])] != "6d6396ed8a103f26c5e295aba62474f5ec65f07206a6b8bf3e4844cce8652f38": raise ValueError("frozen protocol hash mismatch")
    ref, new, rule = [read(p) for p in paths[:3]]
    if rule.get("schema") != "ndt.sleep.independent_descriptive_check.v1": raise ValueError("protocol mismatch")
    if pins[str(paths[3])] != rule["participants_sha256"]: raise ValueError("participant source changed")
    with paths[3].open(encoding="utf-8", newline="") as stream: people = list(csv.DictReader(stream, delimiter="\t"))
    for key, pid_key, summary in (("reference_subject", "reference_pid", ref), ("selected_subject", "participant_pid", new)):
        rows = [r for r in people if r["participant_id"] == rule[key]]
        if len(rows) != 1 or rows[0]["pid"] != rule[pid_key]: raise ValueError("participant identity mismatch")
        source = Path(summary["source"]["path"])
        if source.name != rule[key] + "_Sleep_acq-psg.h5": raise ValueError("summary participant mismatch")
        if sha(source) != summary["source"]["sha256_before"] or summary["source"]["sha256_before"] != summary["source"]["sha256_after"]: raise ValueError("summary source hash mismatch")
    if rule["participant_pid"] == rule["reference_pid"]: raise ValueError("same supplied person ID")
    left, right = contrasts(ref), contrasts(new)
    rows = []
    for key in left:
        x, y = left[key], right[key]
        supported = x["direction"] is not None and y["direction"] is not None
        rows.append({"representation": key[0], "coordinate": key[1], "reference": x, "candidate": y,
                     "direction_agreement": (x["direction"] == y["direction"]) if supported else None})
    if pins != {str(p): sha(p) for p in paths}: raise ValueError("inputs changed")
    result = {"schema": "ndt.sleep.two_parent_direction_check.v1", "status": "descriptive_only",
        "reference_subject": rule["reference_subject"], "candidate_subject": rule["selected_subject"],
        "identity_basis": "distinct pid values in pinned dataset participant metadata",
        "rows": rows, "input_sha256": pins, "code_sha256": sha(__file__),
        "pooling": "not_performed", "p_values": "not_computed", "scientific_qualification": "not_assessed",
        "stage_purity": "not_assessed", "note": "12 correlated coordinates, not independent replications; magnitude units remain recording-relative."}
    destination = Path(output); destination.mkdir(parents=True, exist_ok=False)
    (destination / "parent_direction_comparison.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
    return result

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for key in ("reference", "candidate", "protocol", "participants", "output"): p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args(); run(a.reference,a.candidate,a.protocol,a.participants,a.output)
