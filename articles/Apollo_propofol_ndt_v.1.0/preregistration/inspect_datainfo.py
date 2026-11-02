"""Inspect article-local Cambridge datainfo.mat without assigning H5 phases from run order."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC = ARTICLE_DIR / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apollo_common import DEFAULT_DATAINFO, sha256_file  # noqa: E402
from apollo_g1_labels import load_source_labels  # noqa: E402
from scipy.io import loadmat  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATAINFO
    print(json.dumps({
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "sha256": sha256_file(path) if path.is_file() else None,
    }, indent=2))
    if not path.is_file():
        return 1
    loaded = loadmat(str(path), squeeze_me=True, struct_as_record=False)
    keys = sorted(str(key) for key in loaded if not str(key).startswith("__"))
    raw = loaded.get("datainfo")
    print("mat_keys", keys)
    print("datainfo_type", type(raw).__name__, "shape", getattr(raw, "shape", None))
    labels, report = load_source_labels(path)
    print(json.dumps({
        "status": report.get("status"),
        "n_mat_rows": report.get("n_mat_rows"),
        "n_datainfo_rows": report.get("n_datainfo_rows"),
        "n_subjects": report.get("n_subjects"),
        "n_unparsed_names": report.get("n_unparsed_names"),
        "unparsed_names": report.get("unparsed_names"),
        "depth_order_counts": report.get("depth_order_counts"),
        "failure_reason": report.get("failure_reason"),
        "sample_names": labels["depth_raw_name"].head(8).tolist() if not labels.empty else [],
        "sample_keys": labels[["subject_id", "run", "acq", "protocol_phase_id"]].head(8).to_dict("records")
        if not labels.empty else [],
    }, indent=2, default=str))
    return 0 if report.get("status") in {"labels_loaded", "partial_parse"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
