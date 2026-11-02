"""Independent direct verification; no audit runner or producer imports."""
from pathlib import Path
import hashlib
import json
import h5py
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'results/increment_support_sub99_20260908_r2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


m = json.loads((RUN / 'audit_manifest.json').read_text())
assert m['input_hashes_before'] == m['input_hashes_after']
for name, path in m['inputs'].items():
    assert sha(path) == m['input_hashes_after'][name], name
assert sha(m['config']) == m['config_sha256']
assert sha(RUN / 'output_hashes.json') == (RUN / 'output_hashes.sha256').read_text().split()[0]
for name, digest in json.loads((RUN / 'output_hashes.json').read_text()).items():
    assert sha(RUN / name) == digest
with h5py.File(m['inputs']['input_h5'], 'r') as f:
    ids, t, a, b, stage, raw, x = [f[p][:] for p in ('epoch_id', 'time', 'window_start', 'window_end', 'labels/stage', 'row_source/raw_file', 'coords_3d_subject_anchored/values')]
dt = np.diff(t)
structural = ((np.diff(ids) == 1) & (raw[:-1] == raw[1:]) & (raw[:-1] != b'') &
              np.isfinite(x[:-1]).all(axis=1) & np.isfinite(x[1:]).all(axis=1) &
              np.isfinite(t[:-1]) & np.isfinite(t[1:]) &
              np.isfinite(a[:-1]) & np.isfinite(a[1:]) & np.isfinite(b[:-1]) & np.isfinite(b[1:]) &
              (b[:-1] > a[:-1]) & (b[1:] > a[1:]) & (b[:-1] == a[1:]) &
              (dt > 0) & (np.abs(dt - 30) / 30 <= .05))
same = np.isin(stage[:-1], range(5)) & (stage[:-1] == stage[1:])
pool = pd.read_csv(RUN / 'all_adjacent_pool.csv')
assert len(pool) == len(ids) - 1
np.testing.assert_array_equal(pool.source_index, np.arange(len(ids) - 1))
np.testing.assert_array_equal(pool.target_index, np.arange(1, len(ids)))
np.testing.assert_array_equal(pool.structurally_admissible, structural)
np.testing.assert_array_equal(pool.annotation_eligible, structural & same)
c = pd.read_csv(RUN / 'increment_rows.csv')
q, s, target = [c[col].to_numpy(dtype=int) for col in ('query_index', 'source_index', 'target_index')]
np.testing.assert_array_equal(target, s + 1)
np.testing.assert_array_equal(c.structurally_admissible, structural[s])
np.testing.assert_array_equal(c.same_known_stage, same[s] & (stage[s] == stage[q]) & np.isin(stage[q], range(5)))
queries = pd.read_csv(RUN / 'query_support_summary.csv')
assert queries.full_qualified_count.isna().all() and m['full_qualified_rows'] is None
assert queries.loc[~queries.stage_code.isin(range(5)), 'stage_only_eligible_count'].isna().all()
assert (queries.full_support_status == 'not_assessed').all()
result = {'status': 'PASS', 'run': str(RUN), 'manifest_sha256': sha(RUN / 'audit_manifest.json'),
          'adjacent_pool': len(pool), 'structural_pool': int(structural.sum()),
          'same_known_endpoint_pool': int((structural & same).sum()),
          'stage_endpoint_counts': {str(code): int((structural & same & (stage[:-1] == code)).sum()) for code in range(5)},
          'code8_touching_pairs': int(((stage[:-1] == 8) | (stage[1:] == 8)).sum()),
          'candidate_rows': len(c), 'full_qualified_count': None, 'full_support_status': 'not_assessed'}
(ROOT / 'handover/20260908_increment_coordinator_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
