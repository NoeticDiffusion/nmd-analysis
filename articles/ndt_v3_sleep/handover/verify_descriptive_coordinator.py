"""Independent recomputation from the accepted epoch table, without runner imports."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/descriptive_epoch_sub99_20260907_r10"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


m = json.loads((RUN / "analysis_manifest.json").read_text())
assert sha(RUN / "analysis_manifest.json") == (RUN / "analysis_manifest.sha256").read_text().split()[0]
assert sha(m["analysis_code"]) == m["analysis_code_sha256"]
assert sha(m["config"]["path"]) == m["config"]["sha256"]
assert sha(m["source_table"]) == m["source_sha256"]
assert sha(m["source_epoch_manifest"]) == m["source_epoch_manifest_sha256"]
epoch = json.loads(Path(m["source_epoch_manifest"]).read_text())
assert epoch["output"]["table_sha256"] == m["source_sha256"]
assert sha(epoch["source_h5"]) == epoch["source_sha256_before"] == epoch["source_sha256_after"]
for name, digest in m["output_sha256"].items():
    assert sha(RUN / name) == digest, name

frame = pd.read_parquet(m["source_table"]).sort_values("window_id").reset_index(drop=True)
known = frame.stage_label_status.eq("recorded").to_numpy()
adjacent = (np.diff(frame.window_id) == 1) & np.isclose(
    frame.window_start.to_numpy()[1:], frame.window_end.to_numpy()[:-1], rtol=0, atol=1e-9)
same = (frame.stage_code.to_numpy()[1:] == frame.stage_code.to_numpy()[:-1]) & known[1:] & known[:-1]
interior = np.zeros(len(frame), dtype=bool)
interior[1:-1] = adjacent[:-1] & adjacent[1:] & same[:-1] & same[1:]
coverage = []
checked = 0
for rep, mask in (("3d", "geometry_valid"), ("9d", "coords_9d_valid")):
    columns = [c for c in frame.columns if c.startswith(f"mnps_{rep}_")]
    good = known & np.isfinite(frame[columns].to_numpy()).all(axis=1)
    for leaf in ("coverage_ok", "retained_after_qc", mask):
        good &= frame[f"producer_mask_{leaf}"].eq(1).fillna(False).to_numpy()
    for policy, eligible, filename in (
        ("primary", good, f"coordinate_summary_{rep}.csv"),
        ("boundary", good & interior, f"coordinate_summary_boundary_{rep}.csv"),
    ):
        summary = pd.read_csv(RUN / filename)
        assert len(summary) == 5 * len(columns)
        assert not summary.duplicated(["stage_code", "coordinate"]).any()
        for code in range(5):
            selected = eligible & frame.stage_code.eq(code).to_numpy()
            coverage.append({"representation": rep, "policy": policy, "stage_code": code, "n": int(selected.sum())})
            for column in columns:
                row = summary.loc[(summary.stage_code == code) & (summary.coordinate == column)].iloc[0]
                assert row.n == selected.sum()
                if selected.any():
                    q1, median, q3 = np.percentile(frame.loc[selected, column], [25, 50, 75])
                    np.testing.assert_allclose([row.q1, row["median"], row.q3, row.iqr], [q1, median, q3, q3-q1], rtol=1e-12, atol=1e-12)
                else:
                    assert pd.isna(row[["q1", "median", "q3", "iqr"]]).all()
                checked += 1
record = {
    "status": "PASS", "run": str(RUN), "manifest_sha256": sha(RUN / "analysis_manifest.json"),
    "independent_recomputed_summary_rows": checked, "n_epochs": len(frame),
    "unknown_labels": int((~known).sum()), "coverage": coverage,
    "checks": ["manifest sidecar", "all registered output hashes", "code/config/input/epoch-manifest hashes", "unchanged source HDF5", "independent two-sided boundary membership", "all primary and boundary counts and quartiles"],
    "contract_impact": "article-local descriptive selection only; canonical MNPS unchanged",
    "scientific_qualification": "not_assessed; one-recording development evidence",
    "verification_code_sha256": sha(__file__),
}
(ROOT / "handover/20260907_descriptive_coordinator_validation.json").write_text(json.dumps(record, indent=2), encoding="utf8")
print(json.dumps(record, indent=2))
for filename in ("coordinate_summary_3d.csv", "coordinate_summary_boundary_3d.csv"):
    print(filename)
    print(pd.read_csv(RUN / filename).to_string(index=False))
